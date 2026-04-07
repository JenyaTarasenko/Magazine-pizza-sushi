from django import forms
from .models import Order
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Номер телефона должен быть в формате: '+999999999'"
)

# 1) предоставитьпользователюформузаказа,чтобытотзаполнилеесвои- ми данными;
# 2) создать новый экземпляр Order с введенными данными и создать свя- занный экземпляр OrderItem для каждого товара в корзине;
# 3) очистить все содержимое корзины и перенаправить пользователя на страницу успеха.

class OrderCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Имя",
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите ваше имя',
            'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    last_name = forms.CharField(
        label="Фамилия",
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите вашу фамилию',
            'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Введите ваш email',
            'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    # для Новый почты делаем проверку чтобы пользователь ввел только цифры
    # проверяем в шаблоне
    phone = forms.CharField(
        label="Телефон",
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите номер телефона в формате +380',
            'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'pattern': r'\+?\d+',  # только цифры и + в начале
            'title': 'Введите только цифры',
            'required': True
        })
    )
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone']


def clean_phone(self):
    phone = self.cleaned_data['phone']

    # убираем пробелы
    phone = phone.replace(" ", "")

    if not phone.startswith('+'):
        raise forms.ValidationError("Номер должен начинаться с +")

    return phone


    