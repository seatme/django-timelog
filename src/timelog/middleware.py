import time
import logging
from django.db import connection
from django.utils.encoding import smart_str

logger = logging.getLogger(__name__)

SPLUNK_LOGFORMAT = 'method="{method}" url="{url}" code="{code}" time="{time:.4f}" sqlcount="{sql}" sqltime="{sqltime:.4f}"'
TIMELOG_LOGFORMAT = '%(method)s "%(url)s" (%(code)s) %(time).2f (%(sql)dq, %(sqltime).4f)'

class TimeLogMiddleware(object):

    def process_request(self, request):
        request._start = time.time()

    def process_response(self, request, response):
        # if an exception is occured in a middleware listed
        # before TimeLogMiddleware then request won't have '_start' attribute
        # and the original traceback will be lost (original exception will be
        # replaced with AttributeError)

        sqltime = 0.0
        for q in connection.queries:
            sqltime += float(q.get('time', 0.0) or getattr(q, 'time', 0.0))
        if hasattr(request, '_start'):
            d = {
                'method': request.method,
                'time': time.time() - request._start,
                'code': response.status_code,
                'url': smart_str(request.path_info),
                'sql': len(connection.queries),
                'sqltime': sqltime,
            }
            logger.info(SPLUNK_LOGFORMAT.format(**d))
        return response
