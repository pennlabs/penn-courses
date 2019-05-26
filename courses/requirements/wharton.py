import requests
import unidecode


# Data scraped from https://undergrad-inside.wharton.upenn.edu/course-search-2017/, which gets its
# information from the JSON api located at COURSE_URL

COURSE_URL = 'https://apps.wharton.upenn.edu/reports/index.cfm?action=reports.renderDatatablesJSON&id=UGRGenEdsNew'
columns = ['department', 'course_number', 'title', 'reqs_satisfied', 'ccp']


def _get_requirement_data():
    r = requests.get(COURSE_URL)
    return r.json()['data']


def _parse_ccp(s):
    splits = s.split('-')
    if unidecode.unidecode(splits[0].strip()) == 'No' or unidecode.unidecode(splits[0].strip()) == 'See Advisor':
        return None
    elif unidecode.unidecode(splits[1].strip()) == 'CDUS':
        return ['CCP', 'CDUS']
    else:
        return ['CCP']


def _add_ccp(reqs, ccp):
    result = _parse_ccp(ccp)
    if result is not None:
        reqs.extend(result)


def _clean_data(data):
    cleaned = dict()
    for row in data:
        reqs = row[3].split(',')
        _add_ccp(reqs, row[4])
        reqs = [r for r in reqs if r != 'See Advisor']
        for req in reqs:
            req_list = cleaned.get(req, [])
            req_list.append({
                'department': unidecode.unidecode(row[0]),
                'course_id': row[1],
                'satisfies': True
            })
            cleaned[req] = req_list
    return cleaned


REQUIREMENTS = {
    'CCP': 'Cross-Cultural Perspectives',
    'CDUS': 'Cultural Diversity in the United States',
    'URE': 'Unrestricted Electives',
    'H': 'Humanities',
    'SS': 'Social Science',
    'NSME': 'Natural Sciences, Math, and Engineering',
    'FGE': 'Uncategorized / Flex Gen Ed Only',
}


def get_requirements():
    return {
        'codes': REQUIREMENTS,
        'data': _clean_data(_get_requirement_data()[:10])
    }


if __name__ == '__main__':
    print(get_requirements())

