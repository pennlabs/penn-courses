import json

from jwcrypto import jwt
from rest_framework import permissions

from identity.identity import container, validate_urn


def B2BPermission(urn):
    """
    Create a B2BPermission that only grants access to a product with
    the provided urn.
    """

    class B2BPermissionInner(permissions.BasePermission):
        """
        Grants permission if the current user is a superuser.
        If authentication is successful `request.product` is set
        to the urn of the product making the request.
        """

        def has_permission(self, request, view):
            self.urn = urn
            # Get Authorization header
            authorization = request.META.get("HTTP_AUTHORIZATION")
            if authorization and " " in authorization:
                auth_type, raw_jwt = authorization.split()
                if auth_type == "Bearer":
                    try:
                        # Validate JWT
                        validated_jwt = jwt.JWT(
                            key=container.platform_jwks, jwt=raw_jwt
                        )
                        claims = json.loads(validated_jwt.claims)
                        # Ensure JWT is an access JWT
                        if (
                            "use" in claims
                            and claims["use"] == "access"
                            and "sub" in claims
                        ):
                            # Validate urn (wildcard prefix or exact match)
                            if (
                                self.urn.endswith("*")
                                and claims["sub"].startswith(self.urn[:-1])
                            ) or claims["sub"] == self.urn:
                                # Expose product urn to view
                                request.product = claims["sub"]
                                return True
                    except Exception:
                        return False
            return False

    validate_urn(urn)
    return B2BPermissionInner
