import pytest
from orders.forms import OrderCreateForm


class TestOrderCreateForm:
    """Тесты для формы OrderCreateForm"""

    def test_form_valid_data(self, valid_order_data):
        """Тест валидных данных формы"""
        form = OrderCreateForm(data=valid_order_data)
        assert form.is_valid(), form.errors

    def test_form_all_fields_present(self, valid_order_data):
        """Тест что все поля присутствуют"""
        form = OrderCreateForm(data=valid_order_data)
        assert 'first_name' in form.fields
        assert 'last_name' in form.fields
        assert 'email' in form.fields
        assert 'phone' in form.fields

    def test_form_labels(self, valid_order_data):
        """Тест меток полей"""
        form = OrderCreateForm(data=valid_order_data)
        assert form.fields['first_name'].label == 'Имя'
        assert form.fields['last_name'].label == 'Фамилия'
        assert form.fields['email'].label == 'Email'
        assert form.fields['phone'].label == 'Телефон'

    def test_form_widget_types(self, valid_order_data):
        """Тест типов виджетов"""
        form = OrderCreateForm(data=valid_order_data)
        from django.forms import TextInput, EmailInput
        assert isinstance(form.fields['first_name'].widget, TextInput)
        assert isinstance(form.fields['last_name'].widget, TextInput)
        assert isinstance(form.fields['email'].widget, EmailInput)
        assert isinstance(form.fields['phone'].widget, TextInput)

    def test_form_widget_css_classes(self, valid_order_data):
        """Тест CSS классов виджетов"""
        form = OrderCreateForm(data=valid_order_data)
        widget_class = form.fields['first_name'].widget.attrs.get('class', '')
        assert 'w-full' in widget_class
        assert 'border' in widget_class
        assert 'rounded-md' in widget_class

    def test_form_placeholder_present(self, valid_order_data):
        """Тест плейсхолдеров"""
        form = OrderCreateForm(data=valid_order_data)
        assert 'placeholder' in form.fields['first_name'].widget.attrs
        assert 'placeholder' in form.fields['phone'].widget.attrs

    def test_form_phone_pattern(self, valid_order_data):
        """Тест паттерна телефона"""
        form = OrderCreateForm(data=valid_order_data)
        pattern = form.fields['phone'].widget.attrs.get('pattern', '')
        assert r'\+?\d+' in pattern


class TestOrderCreateFormValidation:
    """Тесты валидации формы"""

    def test_valid_phone_formats(self):
        """Тест валидных форматов телефона"""
        valid_phones = [
            '+380991234567',
            '380991234567',
            '+38099123456789012',
            '1234567890',
        ]
        for phone in valid_phones:
            data = {
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'email': 'test@example.com',
                'phone': phone
            }
            form = OrderCreateForm(data=data)
            assert form.is_valid(), f"Phone {phone} should be valid: {form.errors}"

    def test_invalid_email_no_at(self):
        """Тест email без @"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'testexample.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_email_no_domain(self):
        """Тест email без домена"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_email_no_tld(self):
        """Тест email без TLD"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()

    def test_missing_first_name(self):
        """Тест обязательного поля имя"""
        data = {
            'first_name': '',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_missing_last_name(self):
        """Тест обязательного поля фамилия"""
        data = {
            'first_name': 'Иван',
            'last_name': '',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'last_name' in form.errors

    def test_missing_email(self):
        """Тест обязательного поля email"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': '',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_missing_phone(self):
        """Тест обязательного поля телефон"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': ''
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'phone' in form.errors

    def test_empty_data(self):
        """Тест полностью пустой формы"""
        form = OrderCreateForm(data={})
        assert not form.is_valid()
        assert 'first_name' in form.errors
        assert 'last_name' in form.errors
        assert 'email' in form.errors
        assert 'phone' in form.errors

    def test_first_name_max_length(self):
        """Тест максимальной длины имени"""
        data = {
            'first_name': 'А' * 50,
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_first_name_exceeds_max_length(self):
        """Тест превышения максимальной длины имени"""
        data = {
            'first_name': 'А' * 51,
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_last_name_max_length(self):
        """Тест максимальной длины фамилии"""
        data = {
            'first_name': 'Иван',
            'last_name': 'А' * 50,
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_last_name_exceeds_max_length(self):
        """Тест превышения максимальной длины фамилии"""
        data = {
            'first_name': 'Иван',
            'last_name': 'А' * 51,
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()
        assert 'last_name' in form.errors

    def test_phone_with_letters(self):
        """Тест телефона с буквами"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380ABC123456'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()

    def test_phone_with_special_chars(self):
        """Тест телефона со спецсимволами"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380-99-123-45-67'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()

    def test_email_with_spaces(self):
        """Тест email с пробелами"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test @example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()

    def test_email_unicode_chars(self):
        """Тест email с unicode символами"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@пример.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()


class TestOrderCreateFormEdgeCases:
    """Граничные случаи формы"""

    def test_single_char_first_name(self):
        """Тест однобуквенного имени"""
        data = {
            'first_name': 'И',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_cyrillic_name(self):
        """Тест кириллицы в имени"""
        data = {
            'first_name': 'Пётр',
            'last_name': 'Сидоров',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_latin_name(self):
        """Тест латинских букв в имени"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_mixed_script_name(self):
        """Тест смешанных алфавитов"""
        data = {
            'first_name': 'Александр',
            'last_name': 'Smith',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_name_with_apostrophe(self):
        """Тест апострофа в имени"""
        data = {
            'first_name': "О'Коннор",
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_name_with_hyphen(self):
        """Тест дефиса в имени"""
        data = {
            'first_name': 'Анна-Мария',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_long_phone(self):
        """Тест длинного номера телефона"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+12345678901234567890'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_international_phone(self):
        """Тест международного формата"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@example.com',
            'phone': '+44 20 7946 0958'
        }
        form = OrderCreateForm(data=data)
        assert not form.is_valid()

    def test_email_plus_addressing(self):
        """Тест email с plus addressing"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test+tag@example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_email_subdomain(self):
        """Тест email с subdomain"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'test@mail.example.com',
            'phone': '+380991234567'
        }
        form = OrderCreateForm(data=data)
        assert form.is_valid()

    def test_form_cleaned_data(self, valid_order_data):
        """Тест что cleaned_data содержит правильные данные"""
        form = OrderCreateForm(data=valid_order_data)
        assert form.is_valid()
        cleaned = form.cleaned_data
        assert cleaned['first_name'] == 'Иван'
        assert cleaned['last_name'] == 'Иванов'
        assert cleaned['email'] == 'ivan@example.com'
        assert cleaned['phone'] == '+380991234567'

    def test_form_meta_model(self):
        """Тест что Meta модель установлена правильно"""
        from orders.models import Order
        form = OrderCreateForm()
        assert form._meta.model == Order

    def test_form_meta_fields(self):
        """Тест что Meta fields содержит правильные поля"""
        form = OrderCreateForm()
        assert 'first_name' in form._meta.fields
        assert 'last_name' in form._meta.fields
        assert 'email' in form._meta.fields
        assert 'phone' in form._meta.fields
        assert 'paid' not in form._meta.fields
        assert 'created' not in form._meta.fields
