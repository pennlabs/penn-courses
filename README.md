# shortener

Basic URL shortener as a Django app.

To use:
1. Add this repository as a submodule on the top level of your Django project:
    - `git submodule add https://github.com/pennlabs/shortener.git`
2. Include `shortener.apps.ShortenerConfig` to `INSTALLED_APPS` in your project's `settings.py`
3. Add the shortener to `urls.py`.
    - Example: `path('s/', include('shortener.urls'))` will shorten URLs to `https://example.com/s/<ID>`.
4. `python manage.py migrate`
5. Either add in URL shortcuts manually through Admin, or add some hook in your project to call `shortener.models.shorten`.
The function takes in a long URL and returns a `Url` object which contains the full shortened url as `Url.shortened`, and the slug in `Url.short_id`.
