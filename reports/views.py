# reports/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import UserReportForm
from .models import UserReport

User = get_user_model()


@login_required
def create_user_report(request):
    if request.method == 'POST':
        form = UserReportForm(request.POST)
        if form.is_valid():
            reported_username = form.cleaned_data.get('reported_username')
            reported_user = User.objects.get(username=reported_username)

            # Prevent users from reporting themselves
            if reported_user == request.user:
                messages.error(request, "You cannot report yourself.")
            else:
                report = form.save(commit=False)
                report.reporter = request.user
                report.reported_user = reported_user
                report.save()

                # The confirmation message
                first_name = request.user.first_name or request.user.username
                messages.success(request,
                                 f"Thanks, {first_name}. We have received your report and will review it shortly.")

                return redirect('listings:listing_list')
    else:
        form = UserReportForm()

    return render(request, 'reports/create_report.html', {'form': form})