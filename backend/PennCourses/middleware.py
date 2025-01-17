from accounts.middleware import LoginRequiredMiddleware

class CustomLoginMiddleware(LoginRequiredMiddleware):
    def add_new_exempt_urls(self):
        exempt_urls = []
        
        self.EXEMPT_URLS.extend(exempt_urls)
        # EXAMPLE USAGE
        # self.EXEMPT_URLS.append(r"^accounts/new_exempt_url/$")
        # This can be overriden in the subclass
