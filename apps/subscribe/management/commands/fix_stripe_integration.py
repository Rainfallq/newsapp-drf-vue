import stripe
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.subscribe.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY



class Command(BaseCommand):
    help = 'Fix Stirpe Integration by creating real products and prices'

    def add_arguments(self, parser):
        """
        Добавляет флаг (true/false), чтобы определить создавать ли новый продукт или цену
        """
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate even if stripe_price_id exists'
        )

    def handle(self, *args, **options):
        """Основная логика"""
        force = options['force']

        # Проверяем подключение к stripe
        try:
            stripe.Balance.retrieve()
            self.stdout.write(self.style.SUCCESS('✅ Подключение к Stripe работает'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка подключения к Stripe {e}'))
            return
        
        # Вытаскиваем планы
        plans = SubscriptionPlan.objects.filter(is_active=True)
        
        for plan in plans: 
            self.stdout.write(f'Обрабатываем план: {plan.name}')
            
            # Проверяем нужно ли создавать 
            if plan.stripe_price_id and not force and plan.stripe_price_id.startswith('price_1'):
                self.stdout.write(f' ⏭️ План уже имеет реальный Stripe ID: {plan.stripe_price_id}')
                continue

            try:
                # Создаем или обновляем продукт
                product = stripe.Product.create(
                    name=plan.name,
                    description=f'Subscription plan: {plan.name}',
                    metadata={
                        'plan_id': plan.id,
                        'django_model': 'SubscriptionPlan',
                        'created_by': 'django_management_command'
                    }
                ) 
                self.stdout.write(f' Продукт создан; product id: {product.id}')

                # Создаем цену
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan.price * 100),
                    currency='usd',
                    recurring={'interval': 'month'},
                    metadata={
                        'plan_id': plan.id,
                        'django_model': 'SubscriptionPlan'
                    }
                )
                self.stdout.write(f' Цена создана; price: {price.id}')

                #Обновляем план
                old_id = plan.stripe_price_id
                plan.stripe_price_id = price.id
                plan.save()

                self.stdout.write(self.style.SUCCESS(f'План обновлен {old_id} -> {price.id}'))

            except stripe.error.StripeError as e:
                self.stdout.write(self.style.ERROR(f'Ошибка Stripe для плана {plan.name}: {e}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Общая ошибка для плана {plan.name}: {e}')) 

        self.stdout.write(self.style.SUCCESS(f'Обрабокта завершена! Проверьте Stripe Dashboard'))
