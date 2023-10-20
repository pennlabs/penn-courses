from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.filters import CourseSearchFilterBackend
from courses.models import (
    Attribute,
    Course,
    Friendship,
    NGSSRestriction,
    PreNGSSRequirement,
    Section,
    StatusUpdate,
    User,
)
from courses.search import TypedCourseSearchBackend, TypedSectionSearchBackend
from courses.serializers import (
    AttributeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    FriendshipSerializer,
    MiniSectionSerializer,
    NGSSRestrictionListSerializer,
    PreNGSSRequirementListSerializer,
    SectionDetailSerializer,
    StatusUpdateSerializer,
    UserSerializer,
)
from courses.util import get_current_semester
from PennCourses.docs_settings import PcxAutoSchema
from plan.management.commands.recommendcourses import retrieve_course_clusters, vectorize_user


SEMESTER_PARAM_DESCRIPTION = (
    "The semester of the course (of the form YYYYx where x is A [for spring], "
    "B [summer], or C [fall]), e.g. '2019C' for fall 2019. Alternatively, you "
    "can just pass 'current' for the current semester."
)


class BaseCourseMixin(AutoPrefetchViewSetMixin, generics.GenericAPIView):
    @staticmethod
    def get_semester_field():
        return "semester"

    def get_semester(self):
        semester = self.kwargs.get("semester", "current")
        if semester == "current":
            semester = get_current_semester(allow_not_found=True)
            semester = semester if semester is not None else "all"

        return semester

    def filter_by_semester(self, queryset):
        # if we're in a view without a semester parameter, only return the current semester.
        semester = self.get_semester()
        if semester != "all":
            queryset = queryset.filter(**{self.get_semester_field(): semester})
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_semester(queryset)
        return queryset


class SectionList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of sections (less detailed than [PCx] Section, or SectionDetail on the
    backend).  The sections are filtered by the search term (assumed to be a prefix of a
    section's full code, with each chunk either space-delimited, dash-delimited, or not delimited).
    """

    schema = PcxAutoSchema(
        response_codes={
            "section-search": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Sections Listed Successfully."}
            }
        },
        custom_path_parameter_desc={
            "section-search": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
    )

    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all().exclude(activity="")
    filter_backends = [TypedSectionSearchBackend]
    search_fields = ["^full_code"]

    @staticmethod
    def get_semester_field():
        return "course__semester"

class AutomaticCourseScheduler(generics.ListAPIView, BaseCourseMixin):
   class Scheduler:
        def __init__(self):
            self.intervals = []

        def add_interval(self, start_time, end_time, class_name, section):
            # Adds an interval to the list of intervals
            self.intervals.append((start_time, end_time, class_name, section))
            return True

        def find_optimal_schedule(self):
            # Sort intervals by end time
            sorted_intervals = sorted(self.intervals, key=lambda x: x[1])
            # Initialize variables
            n = len(sorted_intervals)
            dp = [1] * n
            prev = [-1] * n
            # Iterate over sorted intervals
            for i in range(1, n):
                for j in range(i):
                    if sorted_intervals[j][1] <= sorted_intervals[i][0] and sorted_intervals[j][2] != sorted_intervals[i][2]:
                        if dp[j] + 1 > dp[i]:
                            dp[i] = dp[j] + 1
                            prev[i] = j
            # Find the maximum number of non-overlapping intervals
            max_intervals = max(dp)
            # Find the index of the last interval in the optimal schedule
            last_interval_index = dp.index(max_intervals)
            # Build the optimal schedule by backtracking through the prev array
            optimal_schedule = []
            while last_interval_index != -1:
                optimal_schedule.append(sorted_intervals[last_interval_index])
                last_interval_index = prev[last_interval_index]
            optimal_schedule.reverse()
            # Select only one section for each class in the optimal schedule
            selected_classes = set()
            final_schedule = []
            for interval in optimal_schedule:
                class_name = interval[2]
                sections = [i for i in optimal_schedule if i[2] == class_name]
                section = random.choice(sections)
                if class_name not in selected_classes:
                    selected_classes.add(class_name)
                    final_schedule.append(section)
            return final_schedule
            
    def find_sections(courses):
        """
        Separates the lectures and recitations of a certain course into a hash map
        """
        course_to_sections = {}
        for course in courses:
            course_to_sections[course["id"]] = {"LEC": [section for section in course["sections"] if section["activity"] == "LEC"], 
                                                "REC": [section for section in course["sections"] if section["activity"] == "REC"],}
        return course_to_sections

    def find_activities(c_to_s, activity):
        """
        Given a dictionary of courses and their sections, returns a list of only the activities of a certain type (ex: LEC).
        
        Parameters:
        c_to_s (dict): A dictionary of courses and their sections.
        activity (str): The type of activity to filter by (ex: LEC).
        
        Returns:
        list: A list of activities of the specified type.
        """
        activities = []
        for key in c_to_s.keys():
            activities.append(data[key][activity])
        return activities

    def find_lectures_on_day(lectures, day):
        """
        Finds all the lectures on a given day.

        Parameters:
            lectures (list): A list of lectures.
            day (str): The day to search for lectures on.

        Returns:
            list: A list of tuples containing the start time, end time, course code, and section ID for each lecture on the given day.
        """
        lectures_on_day = []
        for lecture in lectures:
            for section in lecture:
                for meeting in section["meetings"]:
                    if meeting["day"] == day:
                        # Adds a randomizer to randomize the order they are fed to the scheduler
                        lectures_on_day.append((meeting["start"], meeting["end"]+0.001*random.random(), "-".join(section["id"].split("-")[0:2]), section["id"] ))
        return lectures_on_day

    def check_overlap(intervals, new_interval):
        """
        Check if a new interval overlaps with any of the existing intervals.

        Parameters:
            intervals (list): A list of intervals, where each interval is a tuple of two integers representing the start and end points of the interval.
            new_interval (tuple): A tuple of two integers representing the start and end points of the new interval.

        Returns:
            bool: True if the new interval does not overlap with any of the existing intervals, False otherwise.
        """
        for interval in intervals:
            if new_interval[0] < interval[1] and new_interval[1] > interval[0]:
                return False
        return True
        
    def schedule_to_section(schedules):
        """
        Given a list of schedules, returns a list of sections by stripping the time intervals from the schedule list.

        Parameters:
            schedules (list): A list of schedules.

        Returns:
            list: A list of sections.
        """
        # Removes the time intervals from the schedule list
        sections = []
        for s in schedules:
            sections.append(s[3])
        return sections

    def remove_duplicates(l):
        """
        Removes duplicates from a list.
        Example:
        remove_duplicates([1,1,1,3,5,7,7]) = [1,3,5,7]
        """
        newl = []
        [newl.append(x) for x in l if x not in newl]
        return newl

    def choose_class_hash(l):
        """
        Given a list of section nodes, chooses one section per class from each schedule randomly.

        Parameters:
            l (list): A list of section nodes.

        Returns:
            list: A list of chosen sections, one per class.
        """
        hash = {}
        courses = []
        for node in l:
            class_name = "-".join(node.split("-")[0:2])
            if class_name not in hash.keys():
                hash[class_name] = [node]
            else:
                hash[class_name].append(node)
        for key in hash.keys():
            # Chooses a random lecture for each class
            courses.append(random.choice(hash[key]))
        return courses

    def check_if_schedule_possible(schedule, courses):
        """
        Given a schedule and a list of courses, checks if the schedule is possible by ensuring that there are no time conflicts
        between the meetings of the courses in the schedule.

        Parameters:
            schedule (list): A list of section IDs representing the courses in the schedule.
            courses (list): A list of dictionaries representing the courses, where each dictionary contains a list of sections.

        Returns:
            bool: True if the schedule is possible, False otherwise.
        """
        intervals = []
        for course in courses:
            for section in course:
                if section["id"] in schedule:
                    for meeting in section["meetings"]:
                        intervals.append((day_to_num[meeting["day"]]+0.01*meeting["start"], day_to_num[meeting["day"]]+0.01*meeting["end"], section["id"]))
        intervals = sorted(intervals, key=lambda x: x[0])
        for i in range(len(intervals)):
            if i == 0:
                continue
            if intervals[i][0] < intervals[i-1][1]:
                return False
        return True

    def scheduler_for_day(lectures, day):
        """
        Takes a list of lectures and a day of the week, and returns a list of unique schedules for that day.
        The schedules are generated by taking 10 samples of possible schedules based on the dynamic programming algorithm.
        """
        day_classes = find_lectures_on_day(lectures, day)
        scheduler = Scheduler()
        for day_class in day_classes:
            scheduler.add_interval(day_class[0], day_class[1], day_class[2], day_class[3])
        day_schedules = []
        for _ in range(10):
            day_schedules.append(scheduler.find_optimal_schedule())
        day_schedules_unique = remove_duplicates(day_schedules)
        return day_schedules_unique

    def add_recs_to_schedule(schedule, recs, lectures):
        """
        Bruteforces recitations into the schedule based on the lectures.

        Parameters:
            schedule (list): A list of strings representing the current schedule.
            recs (list): A list of lists, where each inner list contains dictionaries representing recitation sections for a course.
            lectures (list): A list of lists, where each inner list contains dictionaries representing lecture sections for a course.

        Returns:
            list: A list of strings representing the updated schedule with recitation sections added.

        """
        newschedule = schedule
        for course in recs:
            if course != []:
                course_name = "-".join(course[0]["id"].split("-")[0:2])
                schedule_names = list(map(lambda x: "-".join(x.split("-")[0:2]), schedule))
                if course_name in schedule_names:
                    for section in course:
                        if check_if_schedule_possible(schedule+[section["id"]], recs+lectures):
                            newschedule.append(section["id"])
                            break
        return newschedule

    def find_possible_schedules(courses, count=None):
        """
        Given a list of courses, returns a list of all possible schedules that can be made from those courses.
        If a count is specified, returns only schedules with that many courses.
        """
        c_to_s = find_sections(courses)
        lectures = find_activities(c_to_s, "LEC")
        recs = find_activities(c_to_s, "REC")
        
        monday_schedules = scheduler_for_day(lectures, "M")
        tues_schedules = scheduler_for_day(lectures, "T")
        wed_schedules = scheduler_for_day(lectures, "W")
        thurs_schedules = scheduler_for_day(lectures, "R")
        fri_schedules = scheduler_for_day(lectures, "F")

        possible_mwf = []
        for i in range(len(monday_schedules)):
        for j in range(len(wed_schedules)):
            for k in range(len(fri_schedules)):
                    possible_mwf.append(monday_schedules[i] + wed_schedules[j] + fri_schedules[k])
        
        possible_tr = []
        for i in range(len(tues_schedules)):
            for j in range(len(thurs_schedules)):
                    possible_tr.append(tues_schedules[i] + thurs_schedules[j])

        total_schedules = []
        for i in range(len(possible_tr)):
            for j in range(len(possible_mwf)):
                    total_schedules.append(possible_tr[i] + possible_mwf[j])
        

        courses = list(map(schedule_to_section, total_schedules))
        courses_unique = list(map(remove_duplicates, courses))

        choose = list(map(choose_class_hash, courses_unique))
        choose = [schedule for schedule in choose if check_if_schedule_possible(schedule, lectures)]
        if count != None:
            combinations = []
            for i in range(len(choose)):
                [combinations.append(list(c)) for c in itertools.combinations(choose[i], count) if c not in combinations]
        else:
            combinations = choose
        choose = [add_recs_to_schedule(schedule, recs, lectures) for schedule in combinations]
        choose = sorted(choose, key=lambda x: len(x))
        return choose
        
    
        def create(self, request, *args, **kwargs):
            courses = request.data.get("courses")
            semester = request.data.get("semester")
            queryset = Course.objects.filter(semester=semester, full_code__in=courses).all()
            queryset = queryset.prefetch_related(
                Prefetch(
                    "sections",
                    Section.with_reviews.all()
                ),
                "sections__meetings"
            )
            python_object = CourseListSerializer(queryset, many=True).data
            

class SectionDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course section.
    """

    schema = PcxAutoSchema(
        response_codes={
            "sections-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Section detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            "sections-detail": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
    )

    serializer_class = SectionDetailSerializer
    queryset = Section.with_reviews.all()
    lookup_field = "full_code"

    def get_semester_field(self):
        return "course__semester"


class CourseList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of (all) courses for the provided semester.
    """

    schema = PcxAutoSchema(
        response_codes={
            "courses-list": {"GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}}
        },
        custom_path_parameter_desc={
            "courses-list": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
    )

    serializer_class = CourseListSerializer
    queryset = Course.with_reviews.filter(sections__isnull=False)  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.filter(sections__isnull=False)
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related("course", "meetings__room"),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class CourseListSearch(CourseList):
    """
    This route allows you to list courses by certain search terms and/or filters.
    Without any GET parameters, this route simply returns all courses
    for a given semester. There are a few filter query parameters which constitute ranges of
    floating-point numbers. The values for these are <min>-<max> , with minimum excluded.
    For example, looking for classes in the range of 0-2.5 in difficulty, you would add the
    parameter difficulty=0-2.5. If you are a backend developer, you can find these filters in
    backend/plan/filters.py/CourseSearchFilterBackend. If you are reading the frontend docs,
    these filters are listed below in the query parameters list (with description starting with
    "Filter").
    """

    schema = PcxAutoSchema(
        response_codes={
            "courses-search": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully.",
                    400: "Bad request (invalid query).",
                }
            }
        },
        custom_path_parameter_desc={
            "courses-search": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
    )

    def get_serializer_context(self):
        """
        This method overrides the default `get_serializer_context` (from super class)
        in order to add the `user_vector` and `curr_course_vectors_dict`
        key/value pairs to the serializer context dictionary. If there is no authenticated user
        (ie `self.request.user.is_authenticated` is `False`) or `self.request` is `None`,
        the value associated with the `user_vector` and `curr_course_vectors_dict`key are not set.
        All other key/value pairs that would have been returned by the default
        `get_serializer_context` (which is `CourseList.get_serializer_context`) are in the
        dictionary returned in this method. `user_vector` and `curr_course_vectors_dict` encode the
        vectors used to calculate the recommendation score for a course for a user (see
        `backend/plan/management/commands/recommendcourses.py` for details on the vectors).
        Note that for testing purposes, this implementation of get_serializer_context is replaced
        with simply `CourseList.get_serializer_context` to reduce the costly process of training the
        model in unrelated tests. You can see how this is done and how to override that behavior in
        in `backend/tests/__init__.py`.
        """
        context = super().get_serializer_context()

        if self.request is None or not self.request.user or not self.request.user.is_authenticated:
            return context

        _, _, curr_course_vectors_dict, past_course_vectors_dict = retrieve_course_clusters()
        user_vector, _ = vectorize_user(
            self.request.user, curr_course_vectors_dict, past_course_vectors_dict
        )
        context.update(
            {"user_vector": user_vector, "curr_course_vectors_dict": curr_course_vectors_dict}
        )

        return context

    filter_backends = [TypedCourseSearchBackend, CourseSearchFilterBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course. Includes all details necessary to display course
    info, including requirements this class fulfills, and all sections.
    """

    schema = PcxAutoSchema(
        response_codes={
            "courses-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            "courses-detail": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
    )

    serializer_class = CourseDetailSerializer
    lookup_field = "full_code"
    queryset = Course.with_reviews.all()  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related(
                    "course", "meetings", "associated_sections", "meetings__room", "instructors"
                ),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class PreNGSSRequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of all pre-NGSS (deprecated since 2022C) academic requirements
    in the database for this semester.
    """

    schema = PcxAutoSchema(
        response_codes={
            "requirements-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Requirements listed successfully."}
            },
        },
        custom_path_parameter_desc={
            "requirements-list": {
                "GET": {
                    "semester": (
                        "The semester of the requirement (of the form YYYYx where x is A "
                        "[for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019. "
                        "We organize requirements by semester so that we don't get huge related "
                        "sets which don't give particularly good info."
                    )
                }
            }
        },
    )

    serializer_class = PreNGSSRequirementListSerializer
    queryset = PreNGSSRequirement.objects.all()


class AttributeList(generics.ListAPIView):
    """
    Retrieve a list of unique attributes (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        response_codes={
            "attributes-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Attributes listed successfully."}
            },
        },
    )

    serializer_class = AttributeListSerializer
    queryset = Attribute.objects.all()


class NGSSRestrictionList(generics.ListAPIView):
    """
    Retrieve a list of unique restrictions (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        response_codes={
            "restrictions-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Restrictions listed successfully."}
            },
        },
    )

    serializer_class = NGSSRestrictionListSerializer
    queryset = NGSSRestriction.objects.all()


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    This view exposes the Penn Labs Accounts User object.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user


class StatusUpdateView(generics.ListAPIView):
    """
    Retrieve all Status Update objects from the current semester for a specific section.
    """

    schema = PcxAutoSchema(
        response_codes={
            "statusupdate": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Status Updates for section listed successfully."
                }
            }
        },
        custom_path_parameter_desc={
            "statusupdate": {
                "GET": {
                    "full_code": (
                        "The code of the section which this status update applies to, in the "
                        "form '{dept code}-{course code}-{section code}', e.g. `CIS-120-001` for "
                        "the 001 section of CIS-120."
                    )
                }
            }
        },
    )
    serializer_class = StatusUpdateSerializer
    http_method_names = ["get"]
    lookup_field = "section__full_code"

    def get_queryset(self):
        return StatusUpdate.objects.filter(
            section__full_code=self.kwargs["full_code"],
            section__course__semester=get_current_semester(),
            in_add_drop_period=True,
        ).order_by("created_at")


def get_accepted_friends(user):
    """Return user's accepted friends"""
    return User.objects.filter(
        received_friendships__sender=user, received_friendships__status=Friendship.Status.ACCEPTED
    ) | User.objects.filter(
        sent_friendships__recipient=user, sent_friendships__status=Friendship.Status.ACCEPTED
    )


class FriendshipView(generics.ListAPIView):
    """
    get: Get a list of all friendships and friendship requests (sent and recieved) for the
    specified user. Filter the list by status (accepted, sent) to distinguish between
    friendships and friendship requests.

    post: Create a friendship between two users (sender and recipient). If a previous request does
    not exist between the two friendships, then we create friendship request. If a previous request
    exists (where the recipient is the sender) and the recipient of a request hits this route, then
    we accept the request.

    delete: Delete a friendship between two users (sender and recipient). If there exists only
    a friendship request between two users, then we either delete the friendship request
    if the sender hits the route, or we reject the request if the recipient hits this route.
    """

    #  model = Friendship
    serializer_class = FriendshipSerializer
    http_method_names = ["get", "post", "delete"]
    permission_classes = [IsAuthenticated]

    schema = PcxAutoSchema(
        response_codes={
            "friendship": {
                "GET": {
                    200: "Friendships retrieved successfully.",
                },
                "POST": {
                    201: "Friendship request created successfully.",
                    200: "Friendship request accepted successfully.",
                    409: "Friendship request already exists",
                },
                "DELETE": {
                    200: "Friendship rejected/deleted/cancelled successfully.",
                    404: "Friendship does not exist.",
                    409: "Friendship request already rejected.",
                },
            }
        },
        custom_parameters={
            "friendship": {
                "DELETE": [
                    {
                        "name": "pennkey",
                        "in": "query",
                        "description": "The Pennkey of the user you are ending/rejecting your friendship/friend request with.",  # noqa E501
                        "schema": {"type": "string"},
                        "required": True,
                    },
                ]
            },
        },
        override_request_schema={
            "friendship": {
                "POST": {
                    "type": "object",
                    "properties": {
                        "pennkey": {
                            "type": "string",
                            "description": "The Pennkey of the user you are sending a friend request to or handling a request from.",  # noqa E501
                            "required": True,
                        },
                    },
                }
            }
        },
    )

    # only returns accepted / sent friendships
    def get_queryset(self):
        return Friendship.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
            Q(status=Friendship.Status.ACCEPTED) | Q(status=Friendship.Status.SENT),
        )

    # returns all friendships (regardless of status)
    def get_all_friendships(self):
        return Friendship.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )

    def post(self, request):
        sender = request.user
        recipient = get_object_or_404(User, username=request.data.get("pennkey"))

        existing_friendship = (
            self.get_all_friendships().filter(Q(recipient=recipient) | Q(sender=recipient)).first()
        )

        if not existing_friendship:
            friendship = Friendship(
                sender=sender, recipient=recipient, status=Friendship.Status.SENT
            )
            friendship.save()
            res = FriendshipSerializer(friendship)
            return Response(data=res.data, status=status.HTTP_201_CREATED)
        elif existing_friendship.status == Friendship.Status.REJECTED:
            existing_friendship.status = Friendship.Status.SENT
            existing_friendship.sender = sender
            existing_friendship.recipient = recipient
            existing_friendship.save()
            res = FriendshipSerializer(existing_friendship)
            return Response(data=res.data, status=status.HTTP_200_OK)
        elif existing_friendship.status == Friendship.Status.SENT:
            if existing_friendship.sender == sender:
                return Response({}, status=status.HTTP_409_CONFLICT)
            elif existing_friendship.recipient == sender:
                existing_friendship.status = Friendship.Status.ACCEPTED
                existing_friendship.save()
                res = FriendshipSerializer(existing_friendship)
                return Response(res.data, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_409_CONFLICT)

    def delete(self, request):
        # either deletes a friendship or cancels/rejects a friendship request
        # (depends on who sends the request)
        res = {}
        sender = request.user
        recipient = get_object_or_404(User, username=request.data.get("pennkey"))

        existing_friendship = (
            self.get_all_friendships().filter(Q(recipient=recipient) | Q(sender=recipient)).first()
        )
        if not existing_friendship:
            res["message"] = "Friendship doesn't exist."
            return JsonResponse(res, status=status.HTTP_404_NOT_FOUND)

        if existing_friendship.status == Friendship.Status.ACCEPTED:
            existing_friendship.delete()
            res["message"] = "Friendship deleted successfully."
        elif existing_friendship.status == Friendship.Status.SENT:
            if existing_friendship.sender == sender:
                existing_friendship.delete()
                res["message"] = "Friendship request removed."
            if existing_friendship.recipient == sender:
                existing_friendship.status = Friendship.Status.REJECTED
                existing_friendship.save()
                res["message"] = "Friendship request rejected."
        else:
            res["message"] = "Friendship request already rejected."
            return JsonResponse(res, status=status.HTTP_409_CONFLICT)
        return JsonResponse(res, status=status.HTTP_200_OK)
