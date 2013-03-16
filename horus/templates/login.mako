<html>
  <body>
    <a href="${request.route_url('index')}">Back to Index</a>
    ${render_flash_messages()}
    <h1>Login</h1>
    ${form|n}
    <a href="${request.route_url('forgot_password')}">Forgot Password</a>
  </body>
</html>
