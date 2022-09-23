# from rest_framework.exceptions import NotFound
#
#
# def error404(request, exception):
#     response_data = {'detail': 'PAGE Not found..'}
#     raise NotFound(detail=response_data, code=404)
# from rest_framework.response import Response
#
#
# def custom404(request, exception):
#     return Response({
#         'status_code': 404,
#         'error': 'The resource was not found!!'
#     })
