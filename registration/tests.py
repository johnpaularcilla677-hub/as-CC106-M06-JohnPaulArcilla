from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Student


class StaffAuthenticationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff_user = user_model.objects.create_user(
            username='staff',
            password='test-password-123',
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username='student',
            password='test-password-123',
        )
        self.student = Student.objects.create(
            student_id='S001',
            first_name='Test',
            last_name='Student',
            gender='Male',
            date_of_birth='2000-01-01',
            contact_no='1234567890',
        )

    def test_login_page_and_invalid_credentials(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

        response = self.client.post(
            reverse('login'),
            {'username': 'staff', 'password': 'wrong-password'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_admin_uses_project_login_page_before_access(self):
        response = self.client.get('/admin/')
        self.assertRedirects(
            response,
            '/admin/login/?next=/admin/',
            fetch_redirect_response=False,
        )

        response = self.client.get(response.url)
        self.assertRedirects(
            response,
            '/login/?next=%2Fadmin%2F',
            fetch_redirect_response=False,
        )

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_staff_login_from_admin_returns_to_admin(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'staff',
                'password': 'test-password-123',
                'next': '/admin/',
            },
        )
        self.assertRedirects(response, '/admin/')

        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_log_in_to_admin(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'student',
                'password': 'test-password-123',
                'next': '/admin/',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_registration_links_lead_to_staff_login(self):
        for page_name in ('landing', 'home'):
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                self.assertContains(
                    response,
                    f'href="{reverse("student_registration")}">Register Student</a>',
                )

    def test_staff_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'staff', 'password': 'test-password-123'},
        )
        self.assertRedirects(response, reverse('staff_dashboard'))

        response = self.client.get(reverse('staff_dashboard'))
        self.assertContains(response, 'Welcome, staff!')

    def test_staff_login_returns_to_requested_registration_page(self):
        registration_url = reverse('student_registration')
        response = self.client.post(
            reverse('login'),
            {
                'username': 'staff',
                'password': 'test-password-123',
                'next': registration_url,
            },
        )
        self.assertRedirects(response, registration_url)

        response = self.client.get(registration_url)
        self.assertEqual(response.status_code, 200)

    def test_student_management_views_require_staff(self):
        protected_urls = [
            reverse('staff_dashboard'),
            reverse('student_registration'),
            reverse('student_list'),
            reverse('student_create'),
            reverse('student_detail', args=[self.student.pk]),
            reverse('student_update', args=[self.student.pk]),
            reverse('student_delete', args=[self.student.pk]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('login')))

        self.client.force_login(self.regular_user)
        for url in protected_urls:
            with self.subTest(url=url, user='regular'):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('login')))

    def test_staff_can_access_student_management_views(self):
        self.client.force_login(self.staff_user)
        protected_urls = [
            reverse('staff_dashboard'),
            reverse('student_registration'),
            reverse('student_list'),
            reverse('student_create'),
            reverse('student_detail', args=[self.student.pk]),
            reverse('student_update', args=[self.student.pk]),
            reverse('student_delete', args=[self.student.pk]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_registration_requires_staff_and_staff_can_submit(self):
        registration_url = reverse('student_registration')
        registration_data = {
            'student_id': 'S002',
            'first_name': 'Staff',
            'last_name': 'Registration',
            'gender': 'Female',
            'date_of_birth': '2001-02-03',
            'contact_no': '0987654321',
        }

        response = self.client.get(registration_url)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={registration_url}",
        )

        response = self.client.post(
            registration_url,
            registration_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Student.objects.filter(student_id='S002').exists())

        self.client.force_login(self.staff_user)
        response = self.client.get(registration_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            registration_url,
            registration_data,
        )
        self.assertRedirects(response, reverse('registration_success'))
        self.assertTrue(Student.objects.filter(student_id='S002').exists())

    def test_logout_ends_session_and_protected_views_redirect(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
