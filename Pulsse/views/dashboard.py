from statistics import mean
from flask import Blueprint, jsonify
from datetime import datetime, date, timedelta
from ..database import db
from sqlalchemy import func, extract, and_, desc, text, Integer
from Pulsse.models.visits import Visits
from Pulsse.models.customers import Customers
from flask_jwt_extended import jwt_required
from dateutil.relativedelta import relativedelta

dashboard_blueprint = Blueprint('/dashboard', __name__, url_prefix='/dashboard')


@dashboard_blueprint.route('/dashboard_data/<int:key>', methods=['GET'])
# @jwt_required()
def dashboard_data(key):

    #Customer's Today (Cards data)
    today_date = date.today()

    entered_count = Visits.query.filter(Visits.day == today_date, Visits.sitekey == int(key)).count()
    exited_count = Visits.query.filter(Visits.day == today_date, Visits.time_out.isnot(None), Visits.sitekey == int(key)).count()
    in_store_count = entered_count - exited_count
    groups_count = Visits.query.filter(Visits.day == today_date, Visits.group_val == True, Visits.sitekey == int(key)).count()
    new_customers = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                             .filter(Visits.day == today_date, Customers.created_at == today_date, Visits.sitekey == int(key)) \
                             .count()
    repeating_customers = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                             .filter(Visits.day == today_date, Customers.created_at != today_date, Visits.sitekey == int(key)) \
                             .count()
    customers_today = {'Entered': entered_count, 'Left': exited_count, 'In_store': in_store_count,
                       'Group': groups_count, 'New': new_customers, 'Repeating': repeating_customers}
    

    # Gender Ratio (Pie chart)
    male_count = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                .filter(Visits.day == today_date, Customers.gender == 'male', Visits.sitekey == int(key)) \
                .count()

    female_count = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                .filter(Visits.day == today_date, Customers.gender == 'female', Visits.sitekey == int(key)) \
                .count()
    
    total_users = male_count + female_count
    if total_users > 0:
        male_ratio = male_count / total_users
        female_ratio = female_count / total_users
    else:
        male_ratio = female_ratio = 0
    gender_ratio = {'male_ratio': round(male_ratio,2), 'female_ratio': round(female_ratio,2)}
    

    # Group Ratio
    group_count = Visits.query.filter(Visits.day == today_date, Visits.group_val == True, Visits.sitekey == int(key)).count()
    non_group_count = Visits.query.filter(Visits.day == today_date, Visits.group_val == False, Visits.sitekey == int(key)).count()

    total_group_count = group_count + non_group_count
    if total_group_count > 0:
        group_ratio = group_count / total_group_count
        non_group_ratio = non_group_count / total_group_count
    else:
        group_ratio = non_group_ratio = 0
    group_ratio = {'group_ratio': round(group_ratio,2), 'non_group_ratio': round(non_group_ratio,2)}
    
    
    # Footfall (Daily)
    hourly_counts_time_in = (
        db.session.query(
            func.extract('hour', Visits.time_in).label('hour'),
            func.count(Visits.id).label('count')
        )
            .filter(Visits.day == today_date, Visits.sitekey == int(key))
            .group_by(func.extract('hour', Visits.time_in))
            .order_by(func.extract('hour', Visits.time_in))
            .all()
    )
    result = {
        f'{hour:02}:00-{(hour + 1) % 24:02}:00': {
            'Enter': 0,
            'Exit': 0,
            'Min': 0,
            'Max': 0
        } for hour in range(24)
    }
    hourly_entered_count = [{'hour': int(row.hour), 'count': int(row.count)} for row in hourly_counts_time_in if row.hour is not None]
    hourly_counts_time_out = (
        db.session.query(
            func.extract('hour', Visits.time_out).label('hour'),
            func.count(Visits.id).label('count')
        )
            .filter(Visits.day == today_date, Visits.sitekey == int(key))
            .group_by(func.extract('hour', Visits.time_out))
            .order_by(func.extract('hour', Visits.time_out))
            .all()
    )

    hourly_left_count = [{'hour': int(row.hour), 'count': int(row.count)} for row in hourly_counts_time_out if row.hour is not None]
    for row in hourly_entered_count:
        hour_interval = f'{row["hour"]:02}:00-{(row["hour"] + 1) % 24:02}:00'
        result[hour_interval]['Enter'] = int(row['count'])
    for row in hourly_left_count:
        hour_interval = f'{row["hour"]:02}:00-{(row["hour"] + 1) % 24:02}:00'
        result[hour_interval]['Exit'] = int(row['count'])


    #Footfall (Weekly)
    start_date = date.today() - timedelta(days=date.today().weekday())

    # Initialize the data dictionary
    weekly_data = {'Entered': [], 'Left': [], 'Min': [], 'Max': []}

    # Loop through each day in the week
    for single_date in (start_date + timedelta(n) for n in range(7)):

        # Get the count of people who entered and left the shop on the current day
        entered = (
            db.session.query(func.count(Visits.customer_id))
            .filter(Visits.day == single_date, Visits.sitekey == int(key))
            .scalar()
        )

        left = (
            db.session.query(func.count(Visits.customer_id))
            .filter(and_(Visits.day == single_date, Visits.time_out.isnot(None), Visits.sitekey == int(key)))
            .scalar()
        )

        # Get the min count of people present in the shop at one time on the current day
        subquery_min = (
            db.session.query(
                func.count().label('number_of_customers')
            )
            .filter(Visits.day == single_date, Visits.sitekey == int(key))
            .group_by(extract('hour', Visits.time_in))
            .order_by('number_of_customers')
            .limit(1)
            .subquery()
        )

        min_count = db.session.query(func.coalesce(func.min(subquery_min.c.number_of_customers), 0)).scalar()

        # Get the max count of people present in the shop at one time on the current day
        subquery_max = (
            db.session.query(
                func.count().label('number_of_customers')
            )
            .filter(Visits.day == single_date, Visits.sitekey == int(key))
            .group_by(extract('hour', Visits.time_in))
            .order_by(desc('number_of_customers'))
            .limit(1)
            .subquery()
        )

        max_count = db.session.query(func.coalesce(func.max(subquery_max.c.number_of_customers), 0)).scalar()

        # Append the data to the weekly_data dictionary
        weekly_data['Entered'].append(entered)
        weekly_data['Left'].append(left)
        weekly_data['Min'].append(min_count)
        weekly_data['Max'].append(max_count)


    #Footfall (Monthly)
    current_date = datetime.now()

    # Calculate the date range for the previous month
    first_day_of_current_month = current_date.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

    # Initialize the data dictionary
    monthly_data = {'Entered': [], 'Left': [], 'Min': [], 'Max': []}

    # Loop through each month from the current month to the first month of the year
    current_month = first_day_of_current_month
    while current_month >= first_day_of_previous_month.replace(month=1):
        # Get the count of people who entered and left the shop for the current month
        entered = (
            db.session.query(func.count(Visits.customer_id))
            .filter(
                Visits.sitekey == int(key),
                extract('month', Visits.day) == current_month.month,
                extract('year', Visits.day) == current_month.year,
            )
            .scalar()
        )

        left = (
            db.session.query(func.count(Visits.customer_id))
            .filter(
                Visits.sitekey == int(key),
                extract('month', Visits.day) == current_month.month,
                extract('year', Visits.day) == current_month.year,
                Visits.time_out.isnot(None),
            )
            .scalar()
        )

        min_subquery = (
            db.session.query(
                extract('day', Visits.day).label('day'),
                func.count(Visits.customer_id).label('customer_count')
            )
            .filter(
                Visits.sitekey == int(key),
                extract('month', Visits.day) == current_month.month,
                extract('year', Visits.day) == current_month.year,
            )
            .group_by(extract('day', Visits.day))
            .order_by(text('customer_count'))
            .limit(1)
            .subquery()
        )

        min_count = int(db.session.query(func.sum(min_subquery.c.customer_count)).scalar() or 0)

        # Get the max count of people present in the shop at one time for each day of the month
        max_subquery = (
            db.session.query(
                extract('day', Visits.day).label('day'),
                func.count(Visits.customer_id).label('customer_count')
            )
            .filter(
                Visits.sitekey == int(key),
                extract('month', Visits.day) == current_month.month,
                extract('year', Visits.day) == current_month.year,
            )
            .group_by(extract('day', Visits.day))
            .order_by(text('customer_count DESC'))
            .limit(1)
            .subquery()
        )

        max_count = int(db.session.query(func.sum(max_subquery.c.customer_count)).scalar() or 0)

        # Append the data to the monthly_data dictionary
        monthly_data['Entered'].append(entered or 0)
        monthly_data['Left'].append(left or 0)
        monthly_data['Min'].append(min_count or 0)
        monthly_data['Max'].append(max_count or 0)

        # Move to the previous month
        current_month = current_month - relativedelta(months=1)

    # Reverse the data
    for keys in monthly_data:
        monthly_data[keys] = monthly_data[keys][::-1]

    #Zero for remaining months
    for keys in monthly_data:
        monthly_data[keys] += [0] * (12 - len(monthly_data[keys]))

    today_date = date.today()

    #Table
    print(key)
    all_customers_query = (
        db.session.query(
            Customers,
            Visits.time_in,
            Visits.time_out
        )
        .join(Visits, Customers.id == Visits.customer_id)
        .filter(Visits.sitekey == int(key), Visits.day == today_date)
    )

    # Dictionary to store customer data with max time in
    customer_data = {}

    # Iterate through the results and filter duplicates
    for customer, time_in, time_out in all_customers_query:
        customer_id = customer.id
        if customer_id not in customer_data or time_in > customer_data[customer_id]['latest_time_in']:
            customer_data[customer_id] = {
                'customer_id': customer_id,
                'customer_name': customer.name,
                'gender': customer.gender,
                'latest_time_in': time_in,
                'latest_time_out': time_out,
                'visit_count': 0  # Initialize visit count
            }

    # Now, calculate the total number of visits for each customer
    for customer_id, data in customer_data.items():
        # Perform a new query to get the visit count for each customer
        visit_count = (
            db.session.query(func.count(Visits.id))
            .filter(Visits.customer_id == customer_id, Visits.day == today_date, Visits.sitekey == int(key))
            .scalar()
        )
        customer_data[customer_id]['visit_count'] = visit_count

    # Retrieve the final results
    table_data = []
    for data in customer_data.values():
        table_data.append({
            'customer_id': data['customer_id'],
            'customer_name': data['customer_name'],
            'gender': data['gender'],
            'visit_counts': data['visit_count'],
            'time_in': data['latest_time_in'].strftime('%H:%M:%S') if data['latest_time_in'] else None,
            'time_out': data['latest_time_out'].strftime('%H:%M:%S') if data['latest_time_out'] else None
        })
    

    # Gender Distribution
    current_time = datetime.now().replace(second=0, microsecond=0)
    start_of_day = current_time.replace(hour=0, minute=0)

    # Generate a list of the last 6 hours, including the current hour
    hours_to_query = [start_of_day + timedelta(hours=i) for i in range(current_time.hour, current_time.hour - 6, -1)]

    # Query to get gender counts for each hour
    gender_hourly_counts = (
        db.session.query(
            func.cast(func.extract('hour', Visits.time_in), Integer).label('hour'),  # Explicitly cast to integer
            func.count().filter(Customers.gender == 'Male').label('male_count'),
            func.count().filter(Customers.gender == 'Female').label('female_count')
        )
        .join(Customers, Visits.customer_id == Customers.id)
        .filter(Visits.day == today_date, Visits.sitekey == int(key))
        .filter(func.extract('hour', Visits.time_in).in_([hour.hour for hour in hours_to_query]))
        .group_by(func.cast(func.extract('hour', Visits.time_in), Integer))  # Cast in group_by as well
        .order_by(func.cast(func.extract('hour', Visits.time_in), Integer))  # Cast in order_by as well
        .all()
    )

    # Process results and handle missing hours
    gender_distribution = []

    # Initialize a dictionary to store data for each hour
    hourly_data = {str(hour.hour): {'male_count': 0, 'female_count': 0} for hour in hours_to_query}

    for row in gender_hourly_counts:
        hour = str(row.hour)  # Convert the hour to string
        gender_distribution.append({
            'hour': hour,
            'male_count': row.male_count,
            'female_count': row.female_count,
        })

        # Update the hourly_data dictionary
        hourly_data[hour]['male_count'] = row.male_count
        hourly_data[hour]['female_count'] = row.female_count

    # Ensure all hours in the range are present in the result with counts initialized to zero for missing hours
    for hour in hours_to_query:
        if str(hour.hour) not in [entry['hour'] for entry in gender_distribution]:
            gender_distribution.append({
                'hour': str(hour.hour),
                'male_count': 0,
                'female_count': 0,
            })

    # Sort the result by hour
    gender_distribution.sort(key=lambda x: x['hour'])


    #repeat ratio
    new_customers = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                             .filter(Visits.day == today_date, Customers.created_at == today_date, Visits.sitekey == int(key)) \
                             .distinct(Visits.customer_id) \
                             .count()
    repeat_customers = Customers.query.join(Visits, Customers.id == Visits.customer_id) \
                             .filter(Visits.day == today_date, Customers.created_at != today_date, Visits.sitekey == int(key)) \
                             .distinct(Visits.customer_id) \
                             .count()

    # Prepare the data for the frontend
    repeat_ratio_data = {
        'new_customers': new_customers,
        'repeat_customers': repeat_customers
    }

    #engagement
    stmt = (
            db.session.query(Customers.id, Visits.time_in, Visits.time_out)
            .outerjoin(Visits, (Customers.id == Visits.customer_id) & (Visits.day == today_date))
            .filter(Visits.time_out.isnot(None), Visits.sitekey == key)
        )

    rows = stmt.all()
    # Calculate time spent for each customer in minutes
    time_spent_per_customer = []
    for row in rows:
        customer_id, time_in, time_out = row
        if time_in and time_out:
            time_in_minutes = time_in.hour * 60 + time_in.minute + time_in.second / 60.0
            time_out_minutes = time_out.hour * 60 + time_out.minute + time_out.second / 60.0
            time_spent = time_out_minutes - time_in_minutes
            time_spent_hours = time_spent / 60.0  # Convert to hours
            time_spent_per_customer.append(time_spent_hours)


    # Calculate average, minimum, and maximum time spent
    average_time_spent = mean(time_spent_per_customer) if time_spent_per_customer else 0
    min_time_spent = min(time_spent_per_customer) if time_spent_per_customer else 0
    max_time_spent = max(time_spent_per_customer) if time_spent_per_customer else 0
    
    engagement_data = {
        'max_time': round(max_time_spent, 2),
        'min_time': round(min_time_spent, 2),
        'avg_time': round(average_time_spent, 2)
    }



    final_data = {'customers_today': customers_today, 'gender_ratio': gender_ratio, 'group_ratio': group_ratio,
                  'footfall': result, 'table': table_data, 'gender_distribution': gender_distribution,
                  'repeat_ratio': repeat_ratio_data, 'weekly_data':weekly_data, 'monthly_data': monthly_data, 'engagement':engagement_data}
    
    return jsonify(error=False, msg="Successfully Displayed", Data=final_data), 200


