from courses.views import CourseList, CourseListSearch


def set_mock_get_serializer_context():
    """
    Sets `CourseListSearch.get_serializer_context` to `CourseList.get_serializer_context`
    and returns the original value of `CourseListSearch.get_serializer_context`
    This function is called in `tests.__init__.py` to ensure it takes effect for
    all tests by default. The goal is to reduce testing runtime, though this also means
    that the `recommendation_score` field of the `CourseListSearch` endpoint always returns
    null (`None`) by default in all the tests. However if you would
    like revert to the original (production) version of `CourseListSearch.get_serializer_context`
    it is returned from this function and stored as a package variable as
    production_CourseListSearch_get_serializer_context. To revert to the original version
    for a single test or test case, decorate your test case or test like this:
        ```
        @unittest.mock.patch('courses.views.CourseListSearch.get_serializer_context',
               new=production_CourseListSearch_get_serializer_context)
        ```
    (Note that you should put
    `from tests import production_CourseListSearch_get_serializer_context`
    at the top of the file to make production_CourseListSearch_get_serializer_context
    is defined. Note also that reverting may lead to a `botocore`
    error in the CI tests. To resolve this `botocore` error it is suggested that you patch
    `courses.views.retrieve_course_clusters`. See
     `tests.courses.test_api.CourseSearchRecommendationScoreTestCase.
     test_recommendation_is_number_when_user_is_logged_in` for an example.).
    """
    print(
        "SETTING `CourseListSearch.get_serializer_context` "
        "TO `CourseList.get_serializer_context`...\n"
    )
    production_CourseListSearch_get_serializer_context = CourseListSearch.get_serializer_context
    CourseListSearch.get_serializer_context = CourseList.get_serializer_context
    return production_CourseListSearch_get_serializer_context


# `production_CourseListSearch_get_serializer_context`
# is accessible to all files in the `tests` package (ie, descendants of `backend/tests`)
# and holds the original (production) version of the `CourseListSearch.get_serializer_context`
production_CourseListSearch_get_serializer_context = set_mock_get_serializer_context()
