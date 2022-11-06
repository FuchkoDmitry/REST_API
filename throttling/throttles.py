from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class UserMinRateThrottle(UserRateThrottle):
    scope = 'user_burst'

class UserDayRateThrottle(UserRateThrottle):
    scope = 'user_sustained'

class AnonMinRateThrottle(AnonRateThrottle):
    scope = 'anon_burst'

class AnonDayRateThrottle(AnonRateThrottle):
    scope = 'anon_sustained'