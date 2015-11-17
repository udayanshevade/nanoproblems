from django.shortcuts import render
from django.http import HttpResponse
from problems.models import Tag
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core import serializers

from .models import Problem, Solution
import logic
from .forms import ProblemForm, SolutionForm
from users.logic import is_authenticated, is_authorized
from users.models import User

from comments.forms import CommentForm
from comments.models import Comment
import comments.logic as comments_logic

import problems
import json

import bleach
import markdown


@is_authenticated()
def problems_list(request):
    """ List of all problems. """
    user = User.objects.get(email=request.session['email'])
    print "This is the signed in user we found: ", user.nickname, user.user_key
    latest_problems_list = Problem.objects.order_by('posted')[:10]
    context = {'latest_problems_list': latest_problems_list, 'user': user}
    return render(request, 'problems/problems_list.html', context)


@is_authenticated()
def problem_detail(request, problem_id):
    """ Return the problem details by problem_id. """
    problem = logic.get_problem(problem_id)
    user = User.objects.get(email=request.session['email'])
    solutions_list = Solution.objects.filter(problem=problem)# need to add a way to get all answers to all questions here...
    comments_list = []
    for comment in problem.comments.order_by('-posted'):
        comment.content = markdown.markdown(comment.content, extensions=['markdown.extensions.fenced_code'])
        comments_list.append(comment)

    context = {'problem': problem, 'user_email': request.session['email'], 'solutions_list':solutions_list, 'comments_list': comments_list}
    return render(request, 'problems/problem_detail.html', context)


@is_authenticated()
def new_problem(request):
    """ Create project from user input.

    GET: Return the form to create a project.
    POST: Create a new project and redirect to the project details
    """
    if request.method == "POST":
        # temp = json.loads(request.body)
        form = ProblemForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            problem = form.save(commit=False)
            # fint the user profile object based on the email in session
            user = User.objects.get(email=request.session['email'])
            problem.user = user
            problem.description = bleach.clean(problem.description, strip=True)
            # Save the project object - project needs to exist before
            # manytomany field is accessed.
            problem.save()
            # get the list of tag objects to add to project
            tag_objects_list = logic._get_tags(form.cleaned_data['tags_list'])
            for tag_object in tag_objects_list:
                problem.tags.add(tag_object)
            problem.save()
            # return HttpResponse(str(problem.id))
            return HttpResponseRedirect('/problems/')
        else:
            raise Http404("Form is not valid")
    else:
        # Remove when front end updated.
        form = ProblemForm()
    return render(request, 'problems/new_problem.html', {'form': form})


@is_authenticated()
def new_solution(request, problem_id):
    problem = logic.get_problem(problem_id)
    if request.method == "POST":
        solution_form = SolutionForm(request.POST)
        if solution_form.is_valid():
            # print "The users line is: ", submission_form['members_list']
            solution = solution_form.save(commit=False)
            solution.problem = problem
            user_profile = User.objects.get(email=request.session['email'])
            solution.user = user_profile
            solution.description = bleach.clean(solution.description, strip=True)
            solution.save()
            return HttpResponseRedirect('/problems/' + str(problem_id))
        else:
            raise Http404('Form is not valid')

    else:
        solution_form = SolutionForm()
        return render(request, 'problems/new_solution.html', {'form': solution_form, 'problem_id': problem_id})


@is_authenticated()
def edit_solution(request, problem_id, solution_id):
    print "inside edit_solution"
    solution = logic.get_solution(solution_id)
    if request.method == 'POST':
        print "inside post"
        logic.edit_solution(request, solution)
        return HttpResponseRedirect('/problems/' + str(problem_id) + '/show_solution/' + str(solution_id))
    else:
        form = SolutionForm()
        return render(request, 'problems/edit_solution.html', {'form': form, 'solution': solution, 'problem_id': problem_id})


@is_authenticated()
def delete_solution(request, problem_id, solution_id):
    print "inside edit_solution"
    solution = logic.get_solution(solution_id)
    if request.method == 'POST':
        print "inside post"
        logic.delete_solution(request, solution)
        return HttpResponseRedirect('/problems/' + str(problem_id))
    else:
        return render(request, 'problems/delete_solution.html', {'solution': solution, 'problem_id': problem_id})


@is_authenticated()
def show_solution(request, problem_id, solution_id):
    print "problem_id is: ", problem_id
    print "solution_id is: ", solution_id
    context = logic.get_solution_details(request, problem_id, solution_id)
    return render(request, 'problems/show_solution.html', context)


@is_authenticated()
def add_comment_to_problem(request, problem_id):
    problem = logic.get_problem(problem_id)
    if request.method == 'POST':
        logic.new_comment_problem(request, problem)
    return HttpResponseRedirect('/problems/' + str(problem_id))


@is_authenticated()
def edit_comment_from_problem(request, problem_id, comment_id):
    problem = logic.get_problem(problem_id)
    comment = comments_logic.get_comment(comment_id)
    if request.method == 'POST':
        comment = logic.edit_comment_problem(request, problem, comment_id)
        return HttpResponseRedirect('/problems/' + str(problem_id))
    else:
        comment_form = CommentForm()
    return render(request, 'problems/edit_comment.html',
                  {'form': comment_form, 'problem_id': problem_id, 'comment':comment})  


@is_authenticated()
def delete_comment_from_problem(request, problem_id, comment_id):
    print "inside delete_comment_from_problem"
    problem = Problem.objects.get(pk=problem_id)
    if request.method == 'GET':
        logic.delete_comment_problem(request, problem, comment_id)
    #return problem_detail(request, problem_id)
    return HttpResponseRedirect('/problems/' + str(problem_id))


@is_authenticated()
def add_comment_to_solution(request, problem_id, solution_id):
    print "inside add_comment_to_solution"
    solution = logic.get_solution(solution_id)
    if request.method == 'POST':
        print "request method is post!"
        logic.new_comment_solution(request, solution)
    print "sending to show_solution from add_comment_to_solution"
    return HttpResponseRedirect('/problems/' + str(problem_id) + '/show_solution/' + str(solution_id))


@is_authenticated()
def edit_comment_from_solution(request, problem_id, solution_id, comment_id):
    solution = logic.get_solution(solution_id)
    comment = comments_logic.get_comment(comment_id)
    if request.method == 'POST':
        comment = logic.edit_comment_solution(request, solution, comment_id)
        return HttpResponseRedirect('/problems/' + str(problem_id) + '/show_solution/' + str(solution_id))
    else:
        comment_form = CommentForm()
    return render(request, 'problems/edit_comment_solution.html',
                  {'form': comment_form, 'problem_id':problem_id, 'solution_id': solution_id, 'comment':comment})  


@is_authenticated()
def delete_comment_from_solution(request, problem_id, solution_id, comment_id):
    solution = logic.get_solution(solution_id)
    if request.method == 'GET':
        logic.delete_comment_solution(request, solution, comment_id)
    return HttpResponseRedirect('/problems/' + str(problem_id) + '/show_solution/' + str(solution_id))
