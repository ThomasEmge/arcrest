import cgi
import os.path
import server
import urllib
import urlparse

class Admin(server.RestURL):
    @property
    def clusters(self):
        return self._get_subfolder("./clusters/", Clusters)
    @property
    def directories(self):
        return self._get_subfolder("./system/directories/", Directories)

class Directory(server.RestURL):
   __post__ = True

class Directories(server.RestURL):
    __directories__ = Ellipsis
    @property
    def _directories(self):
        path_and_attribs = [(d['physicalPath'], d) for d in self._json_struct['directories'] ] 
        self.__directories__ = dict(path_and_attribs)
        return self.__directories__
    def __contains__(self, k):
        return self._directories.__contains__(k)
    def __getitem__(self, k):
        return self._directories.__getitem__(k)
    def register(self, type, path, vpath=None, _success=None, _error=None):
        response = self._get_subfolder('./register', Directory,
                                      {'directoryType': type.upper(),
                                       'physicalPath': path,
                                       'virtualPath': vpath})._json_struct
        return not is_json_error(response, _success=_success, _error=_error)
    def unregister(self, path, _success=None, _error=None):
        response = self._get_subfolder('./unregister', Directory,
                                      {'physicalPath': path})._json_struct
        return not is_json_error(response, _success=_success, _error=_error)

class Cluster(server.RestURL):
    __post__ = True
    __lazy_fetch__ = False
    __cache_request__ = True
    def __init__(self, url):
        super(Cluster, self).__init__(url)
        query_dict = dict((k, v[0]) for k, v in 
                               cgi.parse_qs(self.query).iteritems())
        # clusterName indicates the url is for a call to clusters/create
        # so we convert the url to clusters/<clusterName>/
        # and reset the __urldata__ to force a new request
        if "clusterName" in query_dict:
            urlparts = list(self._url)
            urlparts[2] = urlparts[2][0:-1]
            newurl = urlparse.urljoin(self.url, urllib.quote(query_dict["clusterName"] + "/"), False)
            newurl = list(urlparse.urlsplit(newurl))
            newurl[3] = urllib.urlencode({'f':'json'})
            self._url = newurl
            self._clear_cache()
    def delete(self, _error=None):
        response = self._get_subfolder('./delete', Cluster)._json_struct
        return not is_json_error(response, _error=_error)
    def start(self, _error=None, _success=None):
        response = self._get_subfolder('./start', Cluster)._json_struct
        return not is_json_error(response, _error=_error, _success=_success)
    def stop(self):
        response = self._get_subfolder('./stop', Cluster)._json_struct
        return not is_json_error(response)
    def list_machines(self, _error=None, _success=None):
        if not is_json_error(self._json_struct, _error, _success):
            if "machineNames" in self._json_struct:
                return self._json_struct["machineNames"]
    def status(self, _error=None, _success=None):
        self._clear_cache()
        return not is_json_error(self._json_struct, _error, _success)

class Clusters(server.RestURL):
    __post__ = True
    def create(self, cluster_name, machines, _error=None, _success=None):
        cluster = self._get_subfolder('./create', Cluster,
                                     {'clusterName': cluster_name,
                                      'machineNames': machines[0],
                                      'clusterProtocol': 'TCP',
                                      'tcpClusterPort': '4013'})
        if not is_json_error(cluster._json_struct, _error=_error, _success=_success):
            return cluster

def is_json_error(_json, _error=None, _success=None):
    if 'status' in _json and _json['status'] == 'error':
        if _error:
            _error(_json)
        return True
    else:
        if _success:
            _success(_json)
    return False

