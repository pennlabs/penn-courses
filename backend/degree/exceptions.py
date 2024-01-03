from rest_framework import exceptions, status


"""
These custom rest_framework.exceptions.APIException exceptions are used to communicate 
specific validation error details back to the frontend (especially used when handling fulfillments)

In each exception, the detail field should be overriden with a list of violated ids.
"""


class DoubleCountException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    # The default detail should be overriden by a list of violated DoubleCountRestriction ids
    default_detail = "Double count restriction violated."
    default_code = "double_count_violation"


class RuleViolationException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    # Detail should contain a list of violated Rule ids
    default_detail = "Rule not fulfilled."
    default_code = "rule_not_fulfilled"
