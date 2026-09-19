"""Seed the database with demo data for the assessment feature.

Creates one course with one lesson, three questions with their choices, an
instructor, a superuser and a learner account already enrolled in the course,
so the exam can be taken straight away without clicking through the admin.

    python manage.py seed_demo

The command is idempotent: running it again updates the same records instead of
creating duplicates.
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from onlinecourse.models import (
    Choice,
    Course,
    Enrollment,
    Instructor,
    Learner,
    Lesson,
    Question,
)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Admin@12345'
ADMIN_EMAIL = 'admin@example.com'

LEARNER_USERNAME = 'learner'
LEARNER_PASSWORD = 'Learner@12345'

COURSE_NAME = 'Introduction to Django'

# (question_text, grade, [(choice_text, is_correct), ...])
QUESTIONS = [
    (
        'Which Django file maps URL patterns to views?',
        1,
        [
            ('urls.py', True),
            ('models.py', False),
            ('admin.py', False),
            ('settings.py', False),
        ],
    ),
    (
        'Which of the following are valid Django model field types? (select all that apply)',
        2,
        [
            ('CharField', True),
            ('IntegerField', True),
            ('StringBuffer', False),
            ('VarcharField', False),
        ],
    ),
    (
        'Which command applies pending migrations to the database?',
        1,
        [
            ('python manage.py migrate', True),
            ('python manage.py runserver', False),
            ('python manage.py shell', False),
            ('python manage.py collectstatic', False),
        ],
    ),
]


class Command(BaseCommand):
    help = 'Seed demo course, lesson, questions, choices and an enrolled learner.'

    def handle(self, *args, **options):
        admin_user = self._create_superuser()
        instructor = self._create_instructor(admin_user)
        course = self._create_course(instructor)
        lesson = self._create_lesson(course)
        self._create_questions(lesson)
        learner_user = self._create_learner()
        self._enroll(learner_user, course)

        self.stdout.write(self.style.SUCCESS('\nDemo data ready.'))
        self.stdout.write('  Course id     : %s (%s)' % (course.id, course.name))
        self.stdout.write('  Lesson        : %s' % lesson.title)
        self.stdout.write('  Questions     : %s' % course.lesson_set.first().question_set.count())
        self.stdout.write('  Superuser     : %s / %s' % (ADMIN_USERNAME, ADMIN_PASSWORD))
        self.stdout.write('  Learner       : %s / %s' % (LEARNER_USERNAME, LEARNER_PASSWORD))
        self.stdout.write('  Course URL    : http://127.0.0.1:8000/onlinecourse/%s/' % course.id)

    def _create_superuser(self):
        user, created = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={
                'email': ADMIN_EMAIL,
                'first_name': 'Site',
                'last_name': 'Admin',
            },
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(ADMIN_PASSWORD)
        user.save()
        self.stdout.write('%s superuser "%s"' % ('Created' if created else 'Updated', ADMIN_USERNAME))
        return user

    def _create_instructor(self, user):
        instructor, created = Instructor.objects.get_or_create(
            user=user,
            defaults={'full_time': True, 'total_learners': 1},
        )
        self.stdout.write('%s instructor "%s"' % ('Created' if created else 'Reused', instructor))
        return instructor

    def _create_course(self, instructor):
        course, created = Course.objects.get_or_create(
            name=COURSE_NAME,
            defaults={
                'description': 'Learn how Django models, views, templates and the '
                               'admin site fit together, then take the final exam.',
                'pub_date': date.today(),
                'total_enrollment': 0,
                # An image that already ships in static/media/course_images/
                'image': 'course_images/django.png',
            },
        )
        course.instructors.add(instructor)
        self.stdout.write('%s course "%s"' % ('Created' if created else 'Reused', course.name))
        return course

    def _create_lesson(self, course):
        lesson, created = Lesson.objects.get_or_create(
            course=course,
            title='Django Fundamentals',
            defaults={
                'order': 0,
                'content': 'A Django project is organised into apps. Each app holds its '
                           'models (the database layer), its views (the request handling) '
                           'and its templates (the HTML). URLs are routed in urls.py and '
                           'the built-in admin site gives you a CRUD interface for free.',
            },
        )
        self.stdout.write('%s lesson "%s"' % ('Created' if created else 'Reused', lesson.title))
        return lesson

    def _create_questions(self, lesson):
        for question_text, grade, choices in QUESTIONS:
            question, created = Question.objects.get_or_create(
                lesson=lesson,
                question_text=question_text,
                defaults={'grade': grade},
            )
            if not created:
                question.grade = grade
                question.save()
            for choice_text, is_correct in choices:
                choice, _ = Choice.objects.get_or_create(
                    question=question,
                    choice_text=choice_text,
                    defaults={'is_correct': is_correct},
                )
                if choice.is_correct != is_correct:
                    choice.is_correct = is_correct
                    choice.save()
            self.stdout.write('%s question "%s"' % ('Created' if created else 'Reused', question_text))

    def _create_learner(self):
        user, created = User.objects.get_or_create(
            username=LEARNER_USERNAME,
            defaults={'first_name': 'Demo', 'last_name': 'Learner'},
        )
        user.set_password(LEARNER_PASSWORD)
        user.save()
        Learner.objects.get_or_create(
            user=user,
            defaults={'occupation': Learner.STUDENT, 'social_link': 'https://www.example.com'},
        )
        self.stdout.write('%s learner "%s"' % ('Created' if created else 'Updated', LEARNER_USERNAME))
        return user

    def _enroll(self, user, course):
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'mode': Enrollment.HONOR},
        )
        if created:
            course.total_enrollment += 1
            course.save()
        self.stdout.write('%s enrollment of "%s" in "%s"'
                          % ('Created' if created else 'Reused', user.username, course.name))
        return enrollment
