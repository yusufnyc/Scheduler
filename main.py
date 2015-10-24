import web
from web import form

urls=(
	'/', 'Index',
	'/login', 'Login',
	'/register', 'Register',
	'/add', 'Add',
	'/logout', 'Logout',
	'/sms', 'SMS'
)

web.config.debug=False
render=web.template.render('templates/')

app=web.application(urls, globals())



if web.config.get('_session') is None:
	session=web.session.Session(app, web.session.DiskStore('sessions'), initializer={'username': '', 'loggedIn': False})
	web.config._session=session
else:
	session=web.config._session

db=web.database(dbn='mysql', db='scheduler', user='root', pw='a')

class Add:
	addEvent=form.Form
	def GET(self):
		credentials = get_credentials()
		http = credentials.authorize(httplib2.Http())
		service = discovery.build('calendar', 'v3', http=http)

def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'calendar-python-quickstart.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatability with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

class Index:
	def GET(self):
		return render.index(session)

class Logout:
	def GET(self):
		session.kill()
		raise web.seeother('/')

class Login:
	loginForm=form.Form(
		form.Textbox('username', id='username', placeholder='Username')	,
		form.Password('password', id='password', placeholder='Password'),
		form.Button('Submit')
	)
	def GET(self):
		return render.login(self.loginForm)
	def POST(self):
		form=self.loginForm
		if not form.validates():
			return web.seeother('/login')
		else:
			username=form.d.username
			password=form.d.password

		loggedIn=checkAccount(username, password)
		if loggedIn:
			raise web.seeother('/')
		else:
			raise web.seeother('/login')

def checkAccount(username, pw):
	try:
		user=db.query('SELECT * FROM users WHERE username=\'' + username + '\'')[0]
	except IndexError:
		return False

	if not user['password']==pw:
		return False

	session.loggedIn=True
	session.username=user['username']
	session.first=user['firstname']
	session.last=user['lastname']
	return True



class Register:
	registerForm=form.Form(
		form.Textbox('username', id='username', placeholder='Username'),
		form.Password('password', id='password', placeholder='Password'),
		form.Textbox('firstname', id='first', placeholder='First name'),
		form.Textbox('lastname', id='last', placeholder='Last name'),
		form.Textbox('email', id='email', placeholder='Email'),
		form.Button('Submit')
	)
	def GET(self):
		return render.register(self.registerForm)
	def POST(self):
		form=self.registerForm
		if not form.validates():
			return web.seeother('/')
		else:
			username=form.d.username
			password=form.d.password
			first=form.d.firstname
			last=form.d.lastname
			email=form.d.email
			db.insert('users', username=username, password=password, firstname=first, lastname=last, email=email)

class SMS:
	def GET(self):
		response=twiml.Response()
		body=request.form['Body']
		print body
		response.message("Test")
		return str(response)


if __name__=="__main__":
	app.run()