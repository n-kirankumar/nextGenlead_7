from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Integer, Date, Text, DECIMAL, TIMESTAMP, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy.pool import NullPool
import uuid
from datetime import datetime

app = Flask(__name__)

# Database setup
Base = declarative_base()
database_url = "postgresql://postgres:1234@localhost:5432/postgres"
engine = create_engine(database_url, echo=True, poolclass=NullPool)
Session = sessionmaker(bind=engine)
session = Session()


def get_opportunity_stage(probability):
    if 10 <= probability <= 20:
        return "Prospecting"
    elif 21 <= probability <= 40:
        return "Qualification"
    elif 41 <= probability <= 60:
        return "Needs Analysis"
    elif 61 <= probability <= 70:
        return "Value Proposition"
    elif 71 <= probability <= 80:
        return "Decision Makers"
    elif 81 <= probability <= 85:
        return "Perception Analysis"
    elif 86 <= probability <= 90:
        return "Proposal/Price Quote"
    elif 91 <= probability <= 95:
        return "Negotiation/Review"
    elif probability == 100:
        return "Closed Won"
    elif probability == 0:
        return "Closed Lost"
    else:
        return "Unknown Stage"



# Define models for ORM

# Account Model
class Account(Base):
    __tablename__ = 'account'
    account_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_name = Column(String(255), nullable=False)


# Dealer Model
class Dealer(Base):
    __tablename__ = 'dealer'
    dealer_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dealer_code = Column(String(50), nullable=False)
    opportunity_owner = Column(String(255), nullable=False)


# Opportunity Model
class Opportunity(Base):
    __tablename__ = 'opportunity'
    opportunity_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_name = Column(String(255))
    account_id = Column(String, ForeignKey('account.account_id'))
    close_date = Column(Date)
    amount = Column(DECIMAL(10, 2))
    description = Column(Text)
    dealer_id = Column(String, ForeignKey('dealer.dealer_id'))
    dealer_code = Column(String(50))
    dealer_name_or_opportunity_owner = Column(String(255))
    stage = Column(String(50))
    probability = Column(Integer)
    next_step = Column(String(255))
    created_date = Column(TIMESTAMP, default=func.now())

#
# # POST: Create a new customer (opportunity)
# @app.route('/new_customer', methods=['POST'])
# def create_new_customer():
#     payload = request.get_json()
#
#     # Validation for account_name in the account table
#     account = session.query(Account).filter_by(account_name=payload.get('account_name')).first()
#     if not account:
#         return jsonify({"error": "Account does not exist"}), 400
#
#     # Validation for dealer information in the dealer table
#     dealer = session.query(Dealer).filter_by(dealer_id=payload.get('dealer_id'),
#                                              dealer_code=payload.get('dealer_code'),
#                                              opportunity_owner=payload.get('dealer_name_or_opportunity_owner')).first()
#     if not dealer:
#         return jsonify({"error": "Dealer does not exist"}), 400
#
#     # Insert new opportunity record
#     new_opportunity = Opportunity(
#         opportunity_name=payload.get('opportunity_name'),
#         account_id=account.account_id,
#         close_date=payload.get('close_date'),
#         amount=payload.get('amount'),
#         description=payload.get('description'),
#         dealer_id=dealer.dealer_id,
#         dealer_code=payload.get('dealer_code'),
#         dealer_name_or_opportunity_owner=payload.get('dealer_name_or_opportunity_owner'),
#         stage=payload.get('stage'),
#         probability=payload.get('probability'),
#         next_step=payload.get('next_step'),
#         created_date=datetime.now()
#     )
#
#     session.add(new_opportunity)
#     session.commit()
#
#     return jsonify(
#         {"message": "Customer (opportunity) created successfully", "opportunity_id": new_opportunity.opportunity_id})
# POST: Create a new customer (opportunity)
@app.route('/new_customer', methods=['POST'])
def create_new_customer():
    payload = request.get_json()

    # Validation for account_name in the account table
    account = session.query(Account).filter_by(account_name=payload.get('account_name')).first()
    if not account:
        return jsonify({"error": "Account does not exist"}), 400

    # Validation for dealer information in the dealer table
    dealer = session.query(Dealer).filter_by(dealer_id=payload.get('dealer_id'),
                                             dealer_code=payload.get('dealer_code'),
                                             opportunity_owner=payload.get('dealer_name_or_opportunity_owner')).first()
    if not dealer:
        return jsonify({"error": "Dealer does not exist"}), 400

    # Calculate opportunity stage based on probability
    probability = payload.get('probability')
    opportunity_stage = get_opportunity_stage(probability)

    # Insert new opportunity record
    new_opportunity = Opportunity(
        opportunity_name=payload.get('opportunity_name'),
        account_id=account.account_id,
        close_date=payload.get('close_date'),
        amount=payload.get('amount'),
        description=payload.get('description'),
        dealer_id=dealer.dealer_id,
        dealer_code=payload.get('dealer_code'),
        dealer_name_or_opportunity_owner=payload.get('dealer_name_or_opportunity_owner'),
        stage=opportunity_stage,  # Set the calculated stage
        probability=probability,
        next_step=payload.get('next_step'),
        created_date=datetime.now()
    )

    session.add(new_opportunity)
    session.commit()

    return jsonify({"message": "Customer (opportunity) created successfully", "opportunity_id": new_opportunity.opportunity_id})

@app.route('/get_customers', methods=['GET'])
def get_customers():
    dealer_id = request.args.get('dealer_id')
    dealer_code = request.args.get('dealer_code')
    opportunity_owner = request.args.get('opportunity_owner')

    # Validate dealer information
    dealer = session.query(Dealer).filter_by(dealer_id=dealer_id, dealer_code=dealer_code,
                                             opportunity_owner=opportunity_owner).first()
    if not dealer:
        return jsonify({"error": "Dealer does not exist"}), 401

    # Fetch opportunities for the given dealer
    opportunities = session.query(Opportunity).filter_by(dealer_code=dealer_code).all()

    print(f"Opportunities fetched: {opportunities}")  # Debugging print

    return jsonify([{
        "opportunity_name": opp.opportunity_name,
        "account_id": opp.account_id,
        "close_date": opp.close_date,
        "amount": opp.amount,
        "description": opp.description,
        "stage": opp.stage
    } for opp in opportunities])
#
# # GET: Retrieve all customers for a dealer
# @app.route('/get_customers', methods=['GET'])
# def get_customers():
#     dealer_id = request.args.get('dealer_id')
#     dealer_code = request.args.get('dealer_code')
#     opportunity_owner = request.args.get('opportunity_owner')
#
#     # Validate dealer information
#     dealer = session.query(Dealer).filter_by(dealer_id=dealer_id, dealer_code=dealer_code,
#                                              opportunity_owner=opportunity_owner).first()
#     if not dealer:
#         return jsonify({"error": "Dealer does not exist"}), 401
#
#     # Fetch opportunities for the given dealer
#     opportunities = session.query(Opportunity).filter_by(dealer_code=dealer_code).all()
#
#     return jsonify([{
#         "opportunity_name": opp.opportunity_name,
#         "account_id": opp.account_id,
#         "close_date": opp.close_date,
#         "amount": opp.amount,
#         "description": opp.description,
#         "stage": opp.stage
#     } for opp in opportunities])

@app.route('/single-customer', methods=['GET'])
def get_single_customer():
    # Read all the query parameters
    dealer_id = request.args.get('dealer_id')
    dealer_code = request.args.get('dealer_code')
    opportunity_owner = request.args.get('opportunity_owner')
    opportunity_id = request.args.get('opportunity_id')

    # Validate the dealer by checking its existence
    dealer = session.query(Dealer).filter_by(dealer_id=dealer_id, dealer_code=dealer_code,
                                             opportunity_owner=opportunity_owner).first()

    if not dealer:
        return jsonify({"error": "Dealer doesn't exist"}), 401

    # Fetch the opportunity for the given dealer and opportunity ID
    opportunity = session.query(Opportunity).filter_by(opportunity_id=opportunity_id, dealer_id=dealer_id).first()

    if not opportunity:
        return jsonify({"error": "Opportunity not found"}), 404

    # Return the opportunity details as JSON response
    return jsonify({
        "opportunity_id": opportunity.opportunity_id,
        "opportunity_name": opportunity.opportunity_name,
        "account_id": opportunity.account_id,
        "close_date": str(opportunity.close_date),
        "amount": float(opportunity.amount),
        "description": opportunity.description,
        "dealer_id": opportunity.dealer_id,
        "dealer_code": opportunity.dealer_code,
        "dealer_name_or_opportunity_owner": opportunity.dealer_name_or_opportunity_owner,
        "stage": opportunity.stage,
        "probability": opportunity.probability,
        "next_step": opportunity.next_step,
        "created_date": str(opportunity.created_date)
    })


if __name__ == '__main__':
    app.run(debug=True)
