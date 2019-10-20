from django.db.models import Q

from courses.models import Requirement


def requirement_filter(queryset, req_ids, semester):
    query = Q()
    for req_id in req_ids.split(','):
        code, school = req_id.split('@')
        try:
            requirement = Requirement.objects.get(semester=semester, code=code, school=school)
        except Requirement.DoesNotExist:
            continue
        query |= Q(id__in=requirement.satisfying_courses.all())
    queryset = queryset.filter(query)

    return queryset


def bound_filter(field):
    def filter_bounds(queryset, bounds, semester=None):
        lower_bound, upper_bound = bounds.split('-')
        lower_bound = float(lower_bound)
        upper_bound = float(upper_bound)

        return queryset.filter(Q(**{
            f'{field}__gt': lower_bound,
            f'{field}__lte': upper_bound,

        }) | Q(**{f'{field}__isnull': True}))

    return filter_bounds
