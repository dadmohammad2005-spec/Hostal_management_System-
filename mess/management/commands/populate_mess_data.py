from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from mess.models import (
    StudentProfile, MealMenu, MealAttendance, MessFee, FeePayment, MessExpense, Announcement
)

User = get_user_model()


class Command(BaseCommand):
    help = "Populate professional sample data for the Hostel Mess Management System."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Populating comprehensive Hostel Mess Management System sample data..."))

        today = timezone.now().date()

        with transaction.atomic():
            # 1. Fetch or create admin
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser('admin', 'admin@iub.edu.pk', 'admin123')

            # 2. Populate Students
            student_records = [
                {
                    'student_id': 'FA22-BCS-045',
                    'full_name': 'Muhammad Ali Hassan',
                    'department': 'Computer Science',
                    'semester': '5th',
                    'phone_number': '+92-301-2345678',
                    'hostel_room_no': 'Ali Hall Room 101-A',
                    'email': 'ali.hassan@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=90),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-300-1122334 (Father: M. Hassan)',
                },
                {
                    'student_id': 'FA22-BSE-089',
                    'full_name': 'Usman Tariq',
                    'department': 'Software Engineering',
                    'semester': '5th',
                    'phone_number': '+92-302-3456789',
                    'hostel_room_no': 'Ali Hall Room 101-B',
                    'email': 'usman.tariq@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=90),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-301-5566778 (Father: Tariq Mehmood)',
                },
                {
                    'student_id': 'SP23-BIT-018',
                    'full_name': 'Bilal Ahmed',
                    'department': 'Information Technology',
                    'semester': '4th',
                    'phone_number': '+92-303-4567890',
                    'hostel_room_no': 'Ali Hall Room 201-A',
                    'email': 'bilal.ahmed@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=60),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-302-6677889 (Brother: Zohaib)',
                },
                {
                    'student_id': 'FA21-BEE-032',
                    'full_name': 'Hamza Rehman',
                    'department': 'Electrical Engineering',
                    'semester': '7th',
                    'phone_number': '+92-304-5678901',
                    'hostel_room_no': 'Ali Hall Room 301-A',
                    'email': 'hamza.rehman@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=120),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-303-7788990 (Father: Abdul Rehman)',
                },
                {
                    'student_id': 'SP22-MCS-005',
                    'full_name': 'Zeeshan Mehmood',
                    'department': 'Computer Science',
                    'semester': '6th',
                    'phone_number': '+92-305-6789012',
                    'hostel_room_no': 'Ali Hall Room 102-A',
                    'email': 'zeeshan.mehmood@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=75),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-304-8899001 (Uncle: Dr. Shahid)',
                },
                {
                    'student_id': 'FA23-BBA-041',
                    'full_name': 'Abdullah Tahir',
                    'department': 'Management Sciences',
                    'semester': '3rd',
                    'phone_number': '+92-306-7890123',
                    'hostel_room_no': 'Ali Hall Room 201-B',
                    'email': 'abdullah.tahir@student.iub.edu.pk',
                    'joining_date': today - timedelta(days=40),
                    'mess_status': StudentProfile.MessStatus.ACTIVE,
                    'monthly_mess_fee': 4500.00,
                    'emergency_contact': '+92-305-9900112 (Father: Tahir Abbas)',
                },
            ]

            created_students = []
            for s_data in student_records:
                student, _ = StudentProfile.objects.update_or_create(
                    student_id=s_data['student_id'],
                    defaults=s_data
                )
                # Link user account if exists or create
                username = student.student_id.lower()
                user, u_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': student.email,
                        'first_name': student.full_name.split()[0],
                        'last_name': student.full_name.split()[-1],
                    }
                )
                if u_created:
                    user.set_password('student123')
                    if hasattr(user, 'role'):
                        user.role = 'STUDENT'
                    user.save()
                student.user = user
                student.save()
                created_students.append(student)

            # 3. Weekly Menus (Full 7 Days)
            # Find start of current week (Monday)
            start_of_week = today - timedelta(days=today.weekday())

            weekly_meal_schedule = [
                # Monday
                (0, 'MONDAY', 'BREAKFAST', 'Plain Paratha, Omelette / Fried Egg, Karak Chai', '7:30 AM - 9:00 AM', 'Hot tea refill available'),
                (0, 'MONDAY', 'LUNCH', 'Chicken Curry, Steamed Basmati Rice, Fresh Salad, Roti', '12:30 PM - 2:30 PM', 'Fresh salad bar'),
                (0, 'MONDAY', 'EVENING_TEA', 'Black Tea & Bakery Biscuits / Samosa', '5:00 PM - 6:00 PM', ''),
                (0, 'MONDAY', 'DINNER', 'Daal Mash Fry, Seasonal Mix Vegetables, Roti, Kheer', '7:30 PM - 9:30 PM', 'Special dessert night'),

                # Tuesday
                (1, 'TUESDAY', 'BREAKFAST', 'French Toast, Boiled Eggs, Tea / Coffee', '7:30 AM - 9:00 AM', ''),
                (1, 'TUESDAY', 'LUNCH', 'Aloo Palak, Chana Daal Fry, Fresh Roti, Mint Raita', '12:30 PM - 2:30 PM', 'Nutritious green veggies'),
                (1, 'TUESDAY', 'EVENING_TEA', 'Karak Chai & Finger Chips (French Fries)', '5:00 PM - 6:00 PM', ''),
                (1, 'TUESDAY', 'DINNER', 'Beef Shami Kabab with Matar Pulao, Zeera Raita', '7:30 PM - 9:30 PM', 'Student favorite'),

                # Wednesday
                (2, 'WEDNESDAY', 'BREAKFAST', 'Aloo Paratha with Fresh Dahi (Yogurt), Achaar, Tea', '7:30 AM - 9:00 AM', 'Fresh village yogurt'),
                (2, 'WEDNESDAY', 'LUNCH', 'Rajma (Red Kidney Beans Curry) with Steamed Rice, Salad', '12:30 PM - 2:30 PM', ''),
                (2, 'WEDNESDAY', 'EVENING_TEA', 'Tea with Hot Mix Vegetable Pakoras', '5:00 PM - 6:00 PM', ''),
                (2, 'WEDNESDAY', 'DINNER', 'Chicken Qorma, Tandoori Naan, Cucumber Salad', '7:30 PM - 9:30 PM', ''),

                # Thursday
                (3, 'THURSDAY', 'BREAKFAST', 'Khagina (Egg Bhurji), Butter Toast, Jam, Tea', '7:30 AM - 9:00 AM', ''),
                (3, 'THURSDAY', 'LUNCH', 'Kadhi Pakora, Boiled Rice, Fried Green Chillies', '12:30 PM - 2:30 PM', 'Traditional Punjabi Kadhi'),
                (3, 'THURSDAY', 'EVENING_TEA', 'Chai & Vegetable Samosas', '5:00 PM - 6:00 PM', ''),
                (3, 'THURSDAY', 'DINNER', 'Special Chicken Biryani, Special Mint Raita, Cold Drinks', '7:30 PM - 9:30 PM', 'Weekly Biryani Night!'),

                # Friday
                (4, 'FRIDAY', 'BREAKFAST', 'Halwa Puri with Chana Tarkari, Hot Tea', '7:30 AM - 9:30 AM', 'Special Friday Breakfast'),
                (4, 'FRIDAY', 'LUNCH', 'Beef Nihari with Fresh Ginger & Lemon, Roghani Naan', '1:30 PM - 3:00 PM', 'Post-Jumma prayer feast'),
                (4, 'FRIDAY', 'EVENING_TEA', 'Green Tea / Kahwa, Lemonade', '5:00 PM - 6:00 PM', ''),
                (4, 'FRIDAY', 'DINNER', 'Moong Daal Fry, Aloo Gobi, Tandoori Roti', '7:30 PM - 9:30 PM', 'Light healthy dinner'),

                # Saturday
                (5, 'SATURDAY', 'BREAKFAST', 'Cheese Omelette, Paratha, Fresh Milk Tea', '8:00 AM - 10:00 AM', 'Weekend relaxed timings'),
                (5, 'SATURDAY', 'LUNCH', 'Vegetable Fried Rice with Chicken Manchurian', '12:30 PM - 2:30 PM', 'Continental Day'),
                (5, 'SATURDAY', 'EVENING_TEA', 'Tea & Cake Rusk', '5:00 PM - 6:00 PM', ''),
                (5, 'SATURDAY', 'DINNER', 'Chicken Tikka B-B-Q, Paratha, Mint Chutney, Custard', '7:30 PM - 9:30 PM', 'Weekend BBQ night'),

                # Sunday
                (6, 'SUNDAY', 'BREAKFAST', 'Pancakes, Boiled Eggs, Tea / Coffee', '8:30 AM - 10:30 AM', 'Late Sunday Brunch'),
                (6, 'SUNDAY', 'LUNCH', 'Chicken Haleem with Fried Onions, Lemons, Roti', '1:00 PM - 3:00 PM', ''),
                (6, 'SUNDAY', 'EVENING_TEA', 'Chai & Biscuits', '5:00 PM - 6:00 PM', ''),
                (6, 'SUNDAY', 'DINNER', 'Mutton Kofta Curry, Basmati Rice, Roti, Seasonal Fruit', '7:30 PM - 9:30 PM', 'Sunday Grand Dinner'),
            ]

            for offset, day, meal, items, s_time, notes in weekly_meal_schedule:
                menu_date = start_of_week + timedelta(days=offset)
                MealMenu.objects.update_or_create(
                    date=menu_date,
                    meal_type=meal,
                    defaults={
                        'day_of_week': day,
                        'menu_items': items,
                        'serving_time': s_time,
                        'special_instructions': notes,
                        'status': MealMenu.Status.SCHEDULED,
                    }
                )

            # 4. Populate Attendance for Today & Yesterday
            for student in created_students:
                # Yesterday lunch and dinner
                MealAttendance.objects.update_or_create(
                    student=student,
                    date=today - timedelta(days=1),
                    meal_type=MealMenu.MealType.LUNCH,
                    defaults={'status': MealAttendance.AttendanceStatus.PRESENT, 'marked_by': admin_user}
                )
                MealAttendance.objects.update_or_create(
                    student=student,
                    date=today - timedelta(days=1),
                    meal_type=MealMenu.MealType.DINNER,
                    defaults={'status': MealAttendance.AttendanceStatus.PRESENT, 'marked_by': admin_user}
                )
                # Today Breakfast & Lunch
                MealAttendance.objects.update_or_create(
                    student=student,
                    date=today,
                    meal_type=MealMenu.MealType.BREAKFAST,
                    defaults={'status': MealAttendance.AttendanceStatus.PRESENT, 'marked_by': admin_user}
                )
                MealAttendance.objects.update_or_create(
                    student=student,
                    date=today,
                    meal_type=MealMenu.MealType.LUNCH,
                    defaults={'status': MealAttendance.AttendanceStatus.PRESENT, 'marked_by': admin_user}
                )

            # 5. Populate Monthly Mess Fees & Payments
            current_month_name = today.strftime('%B %Y')
            prev_month_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            prev_month_name = prev_month_date.strftime('%B %Y')

            for idx, student in enumerate(created_students):
                # Previous Month Fee (Paid)
                prev_fee, _ = MessFee.objects.update_or_create(
                    student=student,
                    billing_month=prev_month_name,
                    defaults={
                        'month_date': prev_month_date,
                        'total_fee': 4500.00,
                        'amount_paid': 4500.00,
                        'due_date': prev_month_date + timedelta(days=15),
                        'status': MessFee.FeeStatus.PAID,
                    }
                )
                FeePayment.objects.get_or_create(
                    mess_fee=prev_fee,
                    student=student,
                    defaults={
                        'amount': 4500.00,
                        'payment_date': prev_month_date + timedelta(days=8),
                        'payment_method': FeePayment.PaymentMethod.BANK_TRANSFER,
                        'transaction_id': f'HBL-BWP-{student.id}9922',
                        'received_by': admin_user,
                    }
                )

                # Current Month Fee
                if idx in [0, 1]:  # Fully paid
                    curr_fee, _ = MessFee.objects.update_or_create(
                        student=student,
                        billing_month=current_month_name,
                        defaults={
                            'month_date': today.replace(day=1),
                            'total_fee': 4500.00,
                            'amount_paid': 4500.00,
                            'due_date': today.replace(day=1) + timedelta(days=15),
                            'status': MessFee.FeeStatus.PAID,
                        }
                    )
                    FeePayment.objects.get_or_create(
                        mess_fee=curr_fee,
                        student=student,
                        defaults={
                            'amount': 4500.00,
                            'payment_date': today - timedelta(days=3),
                            'payment_method': FeePayment.PaymentMethod.EASYPAISA,
                            'transaction_id': f'EP-BWP-{student.id}4411',
                            'received_by': admin_user,
                        }
                    )
                elif idx in [2, 3]:  # Partially paid
                    curr_fee, _ = MessFee.objects.update_or_create(
                        student=student,
                        billing_month=current_month_name,
                        defaults={
                            'month_date': today.replace(day=1),
                            'total_fee': 4500.00,
                            'amount_paid': 2000.00,
                            'due_date': today.replace(day=1) + timedelta(days=15),
                            'status': MessFee.FeeStatus.PARTIAL,
                        }
                    )
                    FeePayment.objects.get_or_create(
                        mess_fee=curr_fee,
                        student=student,
                        defaults={
                            'amount': 2000.00,
                            'payment_date': today - timedelta(days=2),
                            'payment_method': FeePayment.PaymentMethod.CASH,
                            'transaction_id': f'CASH-REC-00{student.id}',
                            'received_by': admin_user,
                        }
                    )
                else:  # Unpaid / Overdue
                    MessFee.objects.update_or_create(
                        student=student,
                        billing_month=current_month_name,
                        defaults={
                            'month_date': today.replace(day=1),
                            'total_fee': 4500.00,
                            'amount_paid': 0.00,
                            'due_date': today.replace(day=1) + timedelta(days=15),
                            'status': MessFee.FeeStatus.UNPAID,
                        }
                    )

            # 6. Populate Mess Expenses
            expenses = [
                ('FOOD', 'Fresh Chicken Purchasing (60 kg)', 33000.00, today - timedelta(days=2), 'Al-Rehman Poultry Mart, Model Town Bahawalpur'),
                ('GROCERY', 'Super Basmati Rice 100 kg & Atta/Flour 200 kg', 45000.00, today - timedelta(days=5), 'Bismillah Traders, Grain Market Bahawalpur'),
                ('FOOD', 'Fresh Milk (120 Litres) & Fresh Yogurt Dahi', 22800.00, today - timedelta(days=3), 'Sadiq Dairy Farm, Baghdad Road'),
                ('UTILITY', 'Commercial LPG Gas Cylinders Refill (3 Cylinders)', 28500.00, today - timedelta(days=6), 'Pak Gas Agency, University Road'),
                ('GROCERY', 'Cooking Oil (50 Litres) & Mixed Spices/Masalay', 26000.00, today - timedelta(days=8), 'Madina Cash & Carry, Bahawalpur'),
                ('OTHER', 'Kitchen Cleaning Supplies & Detergents', 4500.00, today - timedelta(days=1), 'Ali Hall Mess Store Purchase'),
            ]

            for cat, title, amt, exp_d, desc in expenses:
                MessExpense.objects.get_or_create(
                    title=title,
                    expense_date=exp_d,
                    defaults={
                        'category': cat,
                        'amount': amt,
                        'description': desc,
                        'recorded_by': admin_user,
                    }
                )

            # 7. Populate Announcements
            announcements = [
                (
                    'Special Chicken Biryani Feast & Ice Cream on Thursday Dinner',
                    Announcement.Category.SPECIAL_MEAL,
                    Announcement.Priority.IMPORTANT,
                    'All resident students are informed that the weekly special Biryani night with chilled cold drinks and dessert will be served on Thursday from 7:30 PM to 9:30 PM. Please ensure your attendance is marked on time.',
                    today - timedelta(days=1)
                ),
                (
                    'Monthly Mess Fee Submission Deadline: 15th of Every Month',
                    Announcement.Category.FEE,
                    Announcement.Priority.URGENT,
                    'Resident students are reminded to submit their monthly mess fees before the 15th to avoid late fee surcharges. Payments can be submitted at the Ali Hall accounts counter or via online banking (HBL / EasyPaisa / 1-Bill).',
                    today - timedelta(days=4)
                ),
                (
                    'Friday Post-Jumma Nihari & Dining Timing Adjustment',
                    Announcement.Category.TIMING,
                    Announcement.Priority.NORMAL,
                    'On Fridays, lunch service starts immediately following Jumma prayers at 1:30 PM and remains open until 3:00 PM. Special Beef Nihari with Roghani Naan will be served.',
                    today - timedelta(days=6)
                ),
            ]

            for title, cat, prio, content, pub_date in announcements:
                Announcement.objects.get_or_create(
                    title=title,
                    defaults={
                        'category': cat,
                        'priority': prio,
                        'content': content,
                        'published_date': pub_date,
                        'is_active': True,
                        'posted_by': admin_user,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Hostel Mess sample data populated successfully!"))
        self.stdout.write(self.style.SUCCESS("Admin Login: username='admin', password='admin123'"))
        self.stdout.write(self.style.SUCCESS("Student Login: username='fa22-bcs-045', password='student123'"))
        self.stdout.write(self.style.SUCCESS("Student Login: username='fa22-bse-089', password='student123'"))
