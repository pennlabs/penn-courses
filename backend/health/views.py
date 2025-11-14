from http import HTTPStatus

from django.http import JsonResponse
from django.views.generic import View


class HealthView(View):
    def get(self, request):
        """
        Health check endpoint to confirm the backend is running.
        ---
        summary: Health Check
        responses:
            "200":
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                message:
                                    type: string
                                    enum: ["OK"]
        ---
        """
        return JsonResponse({"message": "OK"}, status=HTTPStatus.OK)
