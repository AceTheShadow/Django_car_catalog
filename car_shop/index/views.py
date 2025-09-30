from django.contrib.auth import login
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.views.generic import ListView, DeleteView, CreateView, UpdateView, DetailView
from .models import Car, Image
from .models.user import UserForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory
from django.db import transaction
from django.contrib import messages


def home(request):
    cars = Car.objects.all()

    return render(request, 'index/home.html', {'cars': cars})


# Inline formset for images
CarImageFormSet = inlineformset_factory(
    Car,
    Image,
    fields=['name', 'is_primary'],
    extra=3,
    can_delete=True
)

class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    fields = ['make', 'model', 'body_type', 'color', 'fuel_type', 'gearbox_type', 'mileage', 'engine_capacity', 'year', 'price', 'description']
    template_name = 'index/car_form.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['image_formset'] = CarImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = CarImageFormSet()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        image_formset = CarImageFormSet(request.POST, request.FILES)

        if form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.owner = request.user
                self.object.save()
                image_formset.instance = self.object
                image_formset.save()
            # messages.success(request, "Car created successfully.")
            return redirect(self.get_success_url())

        # Collect and show validation errors
        # if not form.is_valid():
        #     messages.error(request, "Please correct the errors in the car form.")
        # if not image_formset.is_valid():
        #     messages.error(request, "Please correct the errors in the images section.")
        return self.form_invalid(form)

    def form_invalid(self, form):
        image_formset = CarImageFormSet(self.request.POST, self.request.FILES)
        return self.render_to_response(self.get_context_data(form=form, image_formset=image_formset))

    def get_success_url(self):
        return reverse_lazy('car_detail', kwargs={'pk': self.object.pk})

class CarUpdateView(LoginRequiredMixin, UpdateView):
    model = Car
    fields = ['make', 'model', 'body_type', 'color', 'fuel_type', 'gearbox_type', 'mileage', 'engine_capacity', 'year', 'price', 'description']
    template_name = 'index/car_form.html'
    login_url = 'login'

    def get_queryset(self):
        # Only allow editing cars owned by the current user
        return Car.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['image_formset'] = CarImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['image_formset'] = CarImageFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        image_formset = CarImageFormSet(request.POST, request.FILES, instance=self.object)

        if form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()  # persist make/model/etc.
                image_formset.instance = self.object
                image_formset.save()       # add/update/delete images
            # messages.success(request, "Car updated successfully.")
            return redirect(self.get_success_url())

        # Collect and show validation errors
        # if not form.is_valid():
        #     messages.error(request, "Please correct the errors in the car form.")
        # if not image_formset.is_valid():
        #     messages.error(request, "Please correct the errors in the images section.")
        return self.form_invalid(form)

    def form_invalid(self, form):
        image_formset = CarImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        return self.render_to_response(self.get_context_data(form=form, image_formset=image_formset))

    def get_success_url(self):
        return reverse_lazy('car_detail', kwargs={'pk': self.object.pk})
        # return reverse_lazy('my_cars')

class CarDetailView(DetailView):
    model = Car
    template_name = 'index/car_detail.html'
    context_object_name = 'car'


class CarDeleteView(LoginRequiredMixin, DeleteView):
    model = Car
    template_name = 'index/confirm_delete.html'
    success_url = reverse_lazy('my_cars')

    def get_queryset(self):
        # Restrict deletion to cars owned by the current user
        return Car.objects.filter(owner=self.request.user)


def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # auto login after register
            return redirect('home')
    else:
        form = UserForm()

    # always return a response even if form is invalid
    return render(request, 'index/user/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = "index/user/login.html"

class MyCarsListView(LoginRequiredMixin, ListView):
    model = Car
    template_name = 'index/my_cars.html'
    context_object_name = 'cars'

    def get_queryset(self):
        return Car.objects.filter(owner=self.request.user).prefetch_related(
            Prefetch('images', queryset=Image.objects.filter(is_primary=True))
        )
