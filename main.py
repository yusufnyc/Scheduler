import web, twilio.twiml
from web import form

urls=(
	'/', 'Index',
	'/login', 'Login',
	'/register', 'Register',
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