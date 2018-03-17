#-*- coding:utf-8 -*-
import http.server, os, sys
import subprocess

class base_case(object):
    """docstring for base_file"""

    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            handler.send_content(content)
        except IOError as e:
            e = ("%s cannot be read: %s" % (handler.path, e))
            handler.handle_error(e)

    def index_path(self, handler):
        return os.path.join(handler.full_path, "index.html")

    #要求子类必须实现该接口
    def test(self, handler):
        assert False, 'Not implemented.'

    def act(self, handler):
        assert False, 'Not implemented.'


class ServerException(Exception):
    """服务器内部错误"""
    pass

class case_cgi_file(base_case):
    """脚本文件处理"""
    def run_cgi(self, handler):
        date = subprocess.check_output(["python3", handler.full_path])
        handler.send_content(date)

    def test(self, handler):
        return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')

    def act(self, handler):
        #运行脚本
        self.run_cgi(handler)     

class case_directory_index_file(base_case):
    """docstring for index_path"""
    def test(self, handler):
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

    def act(self, handler):
        self.handle_file(handler ,self.index_path(handler))


class case_no_file(base_case):
    """该路径不存在"""
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("%s not found!" % handler.path)

class case_existing_file(base_case):
    """该路径是文件"""
    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        self.handle_file(handler, handler.full_path)

class case_always_fail(base_case):
    """docstring for case_always_fail"""
    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object %s" % handler.path)                     


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """处理请求，返回页面"""
   
    Error_Page = """\
            <html>
            <body>
            <h1> Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
    """

    #页面模板
    # Page = '''\
    #         <html>
    #         <body>
    #         <table>
    #         <tr>  <td>Header</td>         <td>Value</td>          </tr>
    #         <tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
    #         <tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
    #         <tr>  <td>Client port</td>    <td>{client_port}</td> </tr>
    #         <tr>  <td>Command</td>        <td>{command}</td>      </tr>
    #         <tr>  <td>Path</td>           <td>{path}</td>         </tr>
    #         </table>
    #         </body>
    #         </html>
    #     '''

    Cases = [
        case_no_file(),
        case_cgi_file(),
        case_existing_file(),
        case_directory_index_file(),
        case_always_fail()
        ]
    #处理GET请求
    def do_GET(self):
        try:
            #文件路径完整
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break

            # #如果该路径找不到
            # if not os.path.exists(full_path):
            #     raise ServerException("%s not found!" % self.path)

            # #如果是一个文件，调用hand_file()
            # elif os.path.isfile(full_path):
            #     self.handle_file(full_path)

            # #如果不是一个文件
            # else:
            #     raise ServerException("Unknown object %s" % self.path)

        except Exception as msg:
            self.handle_error(msg)



    # def create_page(self):
    #     values = {
    #         'date_time' : self.date_time_string(),
    #         'client_host' : self.client_address[0],
    #         'client_port' : self.client_address[1],
    #         'command' : self.command,
    #         'path' : self.path,
    #     }
    #     page = self.Page.format(**values)
    #     return page

    def send_content(self, page):
#        page = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


    def handle_error(self, msg):
        content = self.Error_Page.format(path = self.path, msg = msg)
        self.send_content(content.encode())

                                  
#----------------------------------------------------------------

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = http.server.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()