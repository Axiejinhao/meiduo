from django.urls import converters


class UsernameConverter:
    regex = '[a-zA-Z0-9_-]{5,20}'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)


class MobileConverter:
    regex = '1[3-9][0-9]{9}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return str(value)
