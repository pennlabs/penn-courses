from django.db.models import Subquery, OuterRef, Avg

from courses.views import CourseList
from .search import TypedSearchBackend

from courses.models import Requirement
from review.models import ReviewBit
from .serializers import CourseListSearchSerializer


class CourseListSearch(CourseList):
    filter_backends = (TypedSearchBackend, )
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    serializer_class = CourseListSearchSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        req_id = self.request.query_params.get('requirement')
        if req_id is not None:
            code, school = req_id.split('@')
            try:
                requirement = Requirement.objects.get(semester=self.get_semester(), code=code, school=school)
            except Requirement.DoesNotExist:
                return queryset.none()
            queryset = queryset.filter(id__in=requirement.satisfying_courses.all())

        fields = ['course_quality', 'difficulty', 'instructor_quality']

        queryset = queryset.annotate(**{
            field: Subquery(
                ReviewBit.objects.filter(review__section__course__full_code=OuterRef('full_code'),
                                         field=field)
                .values('field')
                .order_by()
                .annotate(avg=Avg('score'))
                .values('avg')[:1]

            )
            for field in fields
        })

        return queryset
