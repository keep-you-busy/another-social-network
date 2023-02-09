from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self):
        titles = [
            'Обо мне',
            'Образование',
            'Личная информация'
        ]

        links = [
            (
                'github',
                'https://github.com/keep-you-busy',
            ),
            (
                'vk',
                'https://vk.com/idefeef8101eb20ede020f5f3e9',
            ),
            (
                'telegram',
                'https://t.me/solutionprogram',
            ),
        ]

        character = [
            (
                'Возраст',
                '24',
            ),
            (
                'Любимое блюдо',
                'бургундские улитки',
            ),
            (
                'Краткое описание',
                'вежлив, правдив, скромен',
            ),
            (
                'Характер',
                'добрый',
            ),
            (
                'Статус',
                'женат',
            ),
            (
                'Местоположение',
                'Таиланд',
            ),
        ]

        education = [
            (
                'Бакалавриат',
                'Инфокоммуникационные технологии и системы связи',
            ),
            (
                'Повышение квалификации',
                'EDA анализ и построение рекомендательной системы'
            ),
        ]

        return {
            'titles': titles,
            'links': links,
            'character': character,
            'education': education
        }


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self):
        links = [
            (
                'Python',
                'https://www.python.org/downloads/',
                'Простоту',
            ),
            (
                'Django',
                'https://www.djangoproject.com/download/',
                'Ясность',
            ),
            (
                'Bootstrap',
                'https://getbootstrap.com/docs/4.0/getting-started/download/',
                'Изящество',
            ),
        ]

        return {
            'links': links
        }
