from django.db.models import Q

from courses.models import Requirement


def requirement_filter(queryset, req_ids, semester):
    query = Q()
    for req_id in req_ids.split('+'):
        code, school = req_id.split('@')
        try:
            requirement = Requirement.objects.get(semester=semester, code=code, school=school)
        except Requirement.DoesNotExist:
            continue
        query |= Q(id__in=requirement.satisfying_courses.all())
    queryset = queryset.filter(query)

    return queryset
