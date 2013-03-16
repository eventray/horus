<html>
  <body>
    <a href="${request.route_url('index')}">Back to Index</a>
    ${render_flash_messages()}
    <h1>Profile</h1>
    ${form|n}
  </body>
</html>
