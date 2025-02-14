from django.http import HttpResponse
from django.shortcuts import render
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from rango.forms import PageForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime


def index(request):
  category_list = Category.objects.order_by('-likes')[:5]
  page_list = Page.objects.order_by('-views')[:5]

  context_dict = {}
  context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
  context_dict['categories'] = category_list
  context_dict['pages'] = page_list

  visitor_cookie_handler(request)
  
  response = render(request, 'rango/index.html', context=context_dict)
  return response

def about(request):

  visitor_cookie_handler(request)

  print(request.session['last_visit'])

  return render(request, 'rango/about.html', {'visits':request.session['visits']})

def show_category(request, category_name_slug):
  print(category_name_slug)
  context_dict = {}

  try:
    category = Category.objects.get(slug=category_name_slug)
    pages = Page.objects.filter(category=category)
    context_dict['pages'] = pages
    context_dict['category'] = category
  except Category.DoesNotExist:
    context_dict['category'] = None
    context_dict['pages'] = None

  return render(request, 'rango/category.html', context=context_dict)

from django.shortcuts import render, redirect
from rango.forms import CategoryForm

@login_required
def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return redirect('/rango/')
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
  try:
    category = Category.objects.get(slug=category_name_slug)
  except Category.DoesNotExist:
    category = None

  if category is None:
    return redirect('/rango/')
  
  form = PageForm()

  if request.method == 'POST':
    form = PageForm(request.POST)
    if form.is_valid():
      if category:
        page = form.save(commit=False)
        page.category = category
        page.views = 0
        page.save()
        return redirect(reverse('rango:show_category',
          kwargs={'category_name_slug':
            category_name_slug}))
    else:
      print(form.errors)

  context_dict = {'form': form, 'category': category}
  return render(request, 'rango/add_page.html', context=context_dict)

def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, 'rango/register.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'registered': registered
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                return render(request, 'rango/login.html', {'error_message': "Your account is disabled."})
        else:
            return render(request, 'rango/login.html', {'error_message': "Invalid login details."})

    return render(request, 'rango/login.html')

@login_required
def restricted(request):
  return render(request, 'rango/restricted.html')

@login_required
def user_logout(request):
  logout(request)
  return redirect(reverse('rango:index'))



# Helper function to retrieve a session cookie safely
def get_server_side_cookie(request, cookie, default_val=None):
  val = request.session.get(cookie)
  if not val:
    val = default_val
  return val

# Visitor tracking function
def visitor_cookie_handler(request):
  visits = get_server_side_cookie(request, 'visits', '1')

  # added checks because errors were showing
  try:
    visits = int(visits) if visits is not None else 1
  except ValueError:
    visits = 1

  last_visit_cookie = get_server_side_cookie(request, 'last_visit', None)

  # added checks because errors were showing
  if last_visit_cookie is None:
    last_visit_time = datetime.now() 
  else:
    try:
      last_visit_time = datetime.strptime(last_visit_cookie, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
      try:
        last_visit_time = datetime.strptime(last_visit_cookie, '%Y-%m-%d %H:%M:%S')
      except ValueError:
        last_visit_time = datetime.now()

  print(last_visit_cookie)
  if (datetime.now() - last_visit_time).days > 0:
    visits = visits + 1

    # Update the last visit cookie now that we have updated the count
    request.session['last_visit'] = str(datetime.now())
  else:
    if last_visit_cookie:
      # Set the last visit cookie
      request.session['last_visit'] = last_visit_cookie
    else:
       request.session['last_visit'] = str(datetime.now())
  # Update/set the visits cookie
  request.session['visits'] = visits