from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
from django.views import generic
from youtubesearchpython import VideosSearch
from googleapiclient.discovery import build
import requests
import json
from PyDictionary import PyDictionary
import wikipedia
from django.contrib.auth.decorators import login_required
from freedictionaryapi.clients.sync_client import DictionaryApiClient

# Create your views here.
def home(request):
    return render(request,'dashboard/home.html')

@login_required
def notes(request):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = Notes(user= request.user, title= request.POST['title'], description= request.POST['description'])
            notes.save()
        messages.success(request,f"Notes Added from {request.user.username} successfully!")
    else:
        form = NotesForm()
    notes = Notes.objects.filter(user=request.user)
    context = {'notes' : notes, 'form' : form}
    return render(request,'dashboard/notes.html', context)

@login_required
def delete_note(request, pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect("notes")

class NotesDetailView(generic.DetailView):
    model = Notes

@login_required
def homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            homeworks = Homework(
                user = request.user,
                subject = request.POST['subject'],
                title = request.POST['title'],
                description = request.POST['description'],
                due = request.POST['due'],
                is_finished = finished
            )
            homeworks.save()
            messages.success(request, f'Homework Added from {request.user.username}!!')
    else:
        form = HomeworkForm()
    homework = Homework.objects.filter(user=request.user)
    if len(homework) == 0:
        homework_done = True
    else:
        homework_done = False
    context = {
                'homeworks' : homework, 
                'homeworks_done' : homework_done,
                'form' : form
                }
    return render(request, 'dashboard/homework.html', context)

@login_required
def update_homework(request,pk=None):
    homework = Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished = False
    else:
        homework.is_finished = True
    homework.save()
    return redirect('homework')

@login_required
def delete_homework(request, pk=None):
    Homework.objects.get(id=pk).delete()
    return redirect("homework")

def youtube(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        video = VideosSearch(text, limit=10)
        result_list = []
        for i in video.result()['result']:
            result_dict = {
                'input' : text,
                'title' : i['title'],
                'duration' : i['duration'],
                'thumbnail' : i['thumbnails'][0]['url'],
                'channel' : i['channel']['name'],
                'link' : i['link'],
                'views' : i['viewCount']['short'],
                'published' : i['publishedTime'],
            }
            desc = ''
            if i['descriptionSnippet']:
                for j in i['descriptionSnippet']:
                    desc += j['text']
            result_dict['description'] = desc
            result_list.append(result_dict)
            context = {
                'form' : form,
                'results' : result_list
            }        
        return render(request, 'dashboard/youtube.html', context)
    else:
        form = DashboardForm()
    context = {'form' : form}
    return render(request, 'dashboard/youtube.html', context)

@login_required
def todo(request):
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False

            todos = Todo(
                user = request.user,
                title = request.POST['title'],
                is_finished = finished
            )
            todos.save()
            messages.success(request, f'Todo Added from {request.user.username}!!')
    else:
        form = TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0 :
        todos_done = True
    else:
        todos_done = False
    context = {
        'todos' : todo,
        'form' : form,
        'todos_done' : todos_done
        }
    return render(request, 'dashboard/todo.html', context)

@login_required
def update_todo(request,pk=None):
    todo = Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo')

@login_required
def delete_todo(request, pk=None):
    Todo.objects.get(id=pk).delete()
    return redirect("todo")

def get_book_info(query):
    # Create a Google Books API client
    service = build('books', 'v1', developerKey='AIzaSyCAY9CrwlMLGLOrV5TgbH92zoxBTQL4yL4')

    # Search for books
    results = service.volumes().list(q=query, maxResults=10).execute()

    # Extract the required fields
    result_list = []
    for item in results['items']:
        title = item['volumeInfo']['title']
        subtitle = item['volumeInfo'].get('subtitle', '')
        description = item['volumeInfo'].get('description', '')
        count = item['volumeInfo'].get('pageCount', '')
        categories = item['volumeInfo'].get('categories', [])
        rating = item['volumeInfo'].get('averageRating', '')
        thumbnail = item['volumeInfo'].get('imageLinks', {}).get('thumbnail', '')
        preview = item['volumeInfo'].get('previewLink','')

        result_dict = {
            'title': title,
            'subtitle': subtitle,
            'description': description,
            'count': count,
            'categories': categories,
            'rating': rating,
            'thumbnail': thumbnail,
            'preview': preview
        }
        result_list.append(result_dict)

    return result_list

def books(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        results = get_book_info(text)

        context = {
            'form' : form,
            'results': results
        }
        return render(request, 'dashboard/books.html', context)
    else:
        form = DashboardForm()
    context = {'form' : form}
    return render(request, 'dashboard/books.html', context)

def dictionary(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        client = DictionaryApiClient()
        parser = client.fetch_parser(text)
        word = parser.word
        
        try:
            phonetics = parser.get_transcription()
            audio = parser.get_link_on_audio_with_pronunciation()
            definition = parser.get_all_definitions()
            examples = parser.get_all_examples()
            synonyms = parser.get_all_synonyms()
            context = {
                'form' : form,
                'input' : text,
                'phonetics' : phonetics,
                'audio' : audio,
                'definitions' : definition,
                'examples' : examples,
                'synonyms' : synonyms
           }
        except:
            context = {
                'form' : form,
                'input' : ''
            }
        return render(request, 'dashboard/dictionary.html', context)
    else:
        form = DashboardForm()
        context = {
                'form' : form,
        }
    return render(request, 'dashboard/dictionary.html', context)

def wiki(request):
    if request.method == "POST":
        text = request.POST['text']
        form = DashboardForm(request.POST)
        search = wikipedia.page(text)
        context = {
            'form' : form,
            'title' : search.title,
            'link' : search.url,
            'details' : search.summary
        }
        return render(request, 'dashboard/wiki.html', context)
    else:
        form = DashboardForm()
        context = {'form' : form}
    return render(request, 'dashboard/wiki.html', context)

def conversion(request):
    if request.method == "POST":
        form = ConversionForm(request.POST)
        if request.POST['measurement'] == 'length':
            measurement_form = ConversionLengthForm()
            context = {
                'form' : form,
                'm_form' : measurement_form,
                'input' : True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'yard' and second == 'foot':
                        answer = f'{input} yard = {int(input)*3} foot'
                    if first == 'foot' and second == 'yard':
                        answer = f'{input} foot = {int(input)/3} yard'
                context = {
                    'form' : form,
                    'm_form' : measurement_form,
                    'input' : True,
                    'answer' : answer
                }
        if request.POST['measurement'] == 'mass':
            measurement_form = ConversionMassForm()
            context = {
                'form' : form,
                'm_form' : measurement_form,
                'input' : True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'pound' and second == 'kilogram':
                        answer = f'{input} pound = {int(input)*0.453592} kilogram'
                    if first == 'kilogram' and second == 'pound':
                        answer = f'{input} kilogram = {int(input)*2.20462} pound'
                context = {
                    'form' : form,
                    'm_form' : measurement_form,
                    'input' : True,
                    'answer' : answer
                }
    else:
        form = ConversionForm()
        context = {
            'form' : form,
            'input' : False
        }
    return render(request, 'dashboard/conversion.html', context)

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    context = {
        'form' : form
    }
    return render(request, 'dashboard/register.html', context)

@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False,user=request.user)
    todos = Todo.objects.filter(is_finished=False,user=request.user)
    if len(homeworks) == 0:
        homework_done = True
    else:
        homework_done = False
    if len(todos) == 0:
        todos_done = True
    else:
        todos_done = False
    context = {
        'homeworks' : homeworks,
        'todos' : todos,
        'homework_done' : homework_done,
        'todos_done' : todos_done
    }
    return render(request, 'dashboard/profile.html', context)
           





