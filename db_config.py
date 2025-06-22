# db_config.py
from pymongo import MongoClient, errors, UpdateOne
import bcrypt
import datetime
import pytz # For timezone handling
import uuid # For generating unique request IDs
from calendar import monthrange # For date calculations

class DBHandler:
    def __init__(self, db_uri="mongodb://localhost:27017/", db_name="staff_management_db"):
        self.daily_sales_collection_name = "daily_sales_records"
        self.users_collection_name = "users"
        self.staff_auth_collection_name = "staff_auth_records"
        self.notifications_collection_name = "notifications"
        self.staff_reports_collection_name = "staff_reports" # General staff reports
        self.approval_requests_collection_name = "approval_requests"
        self.cleaner_inventory_collection_name = "cleaner_inventory_items"
        self.baker_supplies_collection_name = "baker_production_supplies"
        self.baker_daily_logs_collection_name = "baker_daily_logs"
        self.storekeeper_supplies_collection_name = "storekeeper_supplies_items"
        self.cleaner_reports_collection_name = "cleaner_reports" # New
        self.baker_reports_collection_name = "baker_reports" # New (for textual reports from baker)


        try:
            self.client = MongoClient(db_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ismaster') # Check connection
            self.db = self.client[db_name]
            print("Successfully connected to MongoDB.")
        except errors.ServerSelectionTimeoutError as err:
            print(f"MongoDB connection failed: ServerSelectionTimeoutError: {err}")
            self.client = None
            self.db = None
        except errors.ConnectionFailure as err:
            print(f"MongoDB connection failed: ConnectionFailure: {err}")
            self.client = None
            self.db = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            self.db = None

    def get_collection(self, collection_name):
        if self.db is None:
            print("Database not connected. Cannot get collection.")
            return None
        return self.db[collection_name]

    def close_connection(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password, hashed_password_str):
        if plain_password and hashed_password_str:
            try:
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password_str.encode('utf-8'))
            except ValueError:
                print("Error: Invalid hash string provided for password verification.")
                return False
        return False

    def find_staff_auth_record(self, staff_id):
        if self.db is None: return None
        auth_records_collection = self.get_collection(self.staff_auth_collection_name)
        if auth_records_collection is not None:
            return auth_records_collection.find_one({"staff_id": staff_id})
        return None

    def get_user_profile(self, staff_id_or_uid, by_staff_id=True):
        if self.db is None: return None
        users_collection = self.get_collection(self.users_collection_name)
        if users_collection is not None:
            query_field = "staff_id" if by_staff_id else "uid"
            return users_collection.find_one({query_field: staff_id_or_uid})
        return None

    def get_all_user_staff_ids_and_names(self, exclude_roles=None):
        """ Fetches staff IDs and names, optionally excluding certain roles. """
        if self.db is None:
            print("Database not connected.")
            return []
        users_collection = self.get_collection(self.users_collection_name)
        if users_collection is None:
            return []
        try:
            query = {"isActive": True, "staff_id": {"$exists": True}, "name": {"$exists": True}}
            if exclude_roles:
                if isinstance(exclude_roles, str):
                    query["roleName"] = {"$ne": exclude_roles.lower()}
                elif isinstance(exclude_roles, list):
                    query["roleName"] = {"$nin": [r.lower() for r in exclude_roles]}

            staff_details = list(users_collection.find(query, {'staff_id': 1, 'name': 1, '_id': 0}).sort("name", 1))
            return staff_details
        except Exception as e:
            print(f"Error fetching all staff IDs and names: {e}")
            return []


    def get_all_user_staff_ids(self): # Used by notifications
        if self.db is None:
            print("Database not connected.")
            return []
        users_collection = self.get_collection(self.users_collection_name)
        if users_collection is None:
            return []
        try:
            staff_ids = [user['staff_id'] for user in users_collection.find({"isActive": True, "staff_id": {"$exists": True}}, {'staff_id': 1, '_id': 0})]
            return staff_ids
        except Exception as e:
            print(f"Error fetching all staff IDs: {e}")
            return []

    def update_last_login(self, staff_id):
        if self.db is None:
            print(f"Database not connected. Cannot update last login for {staff_id}.")
            return False
        users_collection = self.get_collection(self.users_collection_name)
        if users_collection is not None:
            try:
                result = users_collection.update_one(
                    {"staff_id": staff_id},
                    {"$set": {"last_login_at_utc": datetime.datetime.now(pytz.utc)}}
                )
                if result.modified_count > 0 or result.matched_count > 0:
                    # print(f"Last login updated for staff ID: {staff_id}")
                    return True
                else:
                    # print(f"Could not find staff ID {staff_id} to update last login (matched_count was 0).")
                    return False
            except Exception as e:
                print(f"Error updating last login for {staff_id}: {e}")
                return False
        return False

    def authenticate_user(self, staff_id, password):
        if self.db is None: return None
        auth_record = self.find_staff_auth_record(staff_id)
        if not auth_record:
            # print(f"No auth record found for Staff ID: {staff_id}")
            return None

        if not self.verify_password(password, auth_record.get("hashed_password")):
            # print(f"Password verification failed for Staff ID: {staff_id}")
            return None

        user_uid = auth_record.get("uid")
        if not user_uid:
            # print(f"Auth successful for {staff_id}, but UID missing in auth_record.")
            return {"staff_id": staff_id, "uid": None, "name": "N/A (Profile Error)",
                    "roleName": auth_record.get("role", "N/A"), "isActive": False}

        user_profile = self.get_user_profile(user_uid, by_staff_id=False)
        if not user_profile:
            # print(f"Auth successful for {staff_id}, but no detailed profile found for UID {user_uid}.")
            return {"staff_id": staff_id, "uid": user_uid, "name": "N/A (Profile Missing)",
                    "roleName": auth_record.get("role", "N/A"), "isActive": False}

        if user_profile.get("isActive", False):
            self.update_last_login(staff_id)
        return user_profile

    def update_user_password(self, staff_id, current_plain_password, new_plain_password):
        if self.db is None: return False, "Database not connected."
        auth_record = self.find_staff_auth_record(staff_id)
        if not auth_record:
            return False, f"User with Staff ID {staff_id} not found."
        if not self.verify_password(current_plain_password, auth_record.get("hashed_password")):
            return False, "Incorrect current password."
        try:
            new_hashed_password = self.hash_password(new_plain_password)
            auth_collection = self.get_collection(self.staff_auth_collection_name)
            if auth_collection is None:
                 return False, "Could not access authentication records."

            result = auth_collection.update_one(
                {"staff_id": staff_id},
                {"$set": {
                    "hashed_password": new_hashed_password,
                    "password_last_updated_at": datetime.datetime.now(pytz.utc)
                    }
                }
            )
            if result.modified_count == 1:
                return True, "Password updated successfully."
            return False, "Password not updated (no changes or error)."
        except Exception as e:
            return False, f"Error updating password: {e}"

    def initial_staff_setup(self, staff_id, password, name, email, role_name, department_id=None, added_by_profile=None):
        if self.db is None:
            return False, "Database not connected. Cannot perform setup."

        # Prevent manager from creating/setting role as 'developer'
        if added_by_profile and added_by_profile.get("roleName", "").lower() == "manager" and role_name.lower() == "developer":
            return False, "Managers cannot create staff with the 'developer' role."

        staff_auth_collection = self.get_collection(self.staff_auth_collection_name)
        users_collection = self.get_collection(self.users_collection_name)

        if staff_auth_collection is None or users_collection is None:
            return False, "Could not retrieve necessary collections. Cannot perform setup."

        try:
            if users_collection.find_one({"staff_id": staff_id}):
                # print(f"Staff ID {staff_id} already exists. Skipping setup.")
                return False, f"Staff ID {staff_id} already exists."

            if users_collection.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}}):
                existing_user_by_email = users_collection.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
                # print(f"Email {email} already exists for staff ID {existing_user_by_email.get('staff_id')}. Skipping setup.")
                return False, f"Email {email} already in use."

            hashed_pass = self.hash_password(password)
            user_uid = f"user_{uuid.uuid4()}"

            auth_insert_result = staff_auth_collection.insert_one({
                "staff_id": staff_id, "hashed_password": hashed_pass, "role": role_name.lower(),
                "uid": user_uid, "created_at": datetime.datetime.now(pytz.utc)
            })

            user_insert_result = users_collection.insert_one({
                "uid": user_uid, "staff_id": staff_id, "name": name, "email": email,
                "roleName": role_name.lower(), "departmentId": department_id, "isActive": True,
                "created_at": datetime.datetime.now(pytz.utc), "last_login_at_utc": None
            })
            # print(f"Successfully set up staff: {name} ({staff_id}) with role '{role_name}' and UID {user_uid}")
            return True, f"Staff member {name} ({staff_id}) created successfully."
        except Exception as e:
            error_msg = f"Error during staff setup for {staff_id}: {e}"
            print(error_msg)
            # Attempt to roll back if partially inserted
            if 'auth_insert_result' in locals() and hasattr(auth_insert_result, 'inserted_id') and auth_insert_result.inserted_id:
                staff_auth_collection.delete_one({"_id": auth_insert_result.inserted_id})
            if 'user_insert_result' in locals() and hasattr(user_insert_result, 'inserted_id') and user_insert_result.inserted_id:
                 if 'user_uid' in locals(): users_collection.delete_one({"uid": user_uid}) # Ensure uid exists
            return False, error_msg

    def get_all_staff_except_role(self, excluded_role="developer"):
        if self.db is None: return []
        users_collection = self.get_collection(self.users_collection_name)
        if users_collection is not None:
            try:
                query = {}
                if excluded_role:
                    if isinstance(excluded_role, str): query = {"roleName": {"$ne": excluded_role.lower()}}
                    elif isinstance(excluded_role, list): query = {"roleName": {"$nin": [r.lower() for r in excluded_role]}}
                return list(users_collection.find(query).sort("name", 1))
            except Exception as e:
                print(f"Error retrieving staff list: {e}")
                return []
        return []

    def update_staff_member(self, staff_id, update_data, editor_profile=None):
        if self.db is None: return False, "Database not connected."

        users_collection = self.get_collection(self.users_collection_name)
        staff_auth_collection = self.get_collection(self.staff_auth_collection_name)
        if users_collection is None: return False, "Users collection not found."
        
        target_user_profile = self.get_user_profile(staff_id) # Get current state of target user

        # Security and business logic checks
        if editor_profile:
            editor_role = editor_profile.get("roleName","").lower()
            target_current_role = target_user_profile.get("roleName","").lower() if target_user_profile else ""
            
            if editor_role == "manager":
                # Manager cannot edit 'developer' accounts at all
                if target_current_role == "developer":
                    return False, "Managers cannot edit staff with the 'developer' role."
                # Manager cannot assign 'developer' role
                if update_data.get("roleName","").lower() == "developer":
                    return False, "Managers cannot assign the 'developer' role."
            # Add more role-based restrictions if needed (e.g., developer has full power, supervisor limited)
            # For now, developers can edit other developers unless more rules are added in UI or here

        try:
            if "email" in update_data:
                existing_user_with_email = users_collection.find_one({
                    "email": {"$regex": f"^{update_data['email']}$", "$options": "i"},
                    "staff_id": {"$ne": staff_id}
                })
                if existing_user_with_email:
                    return False, f"Email '{update_data['email']}' is already in use by another staff member."
            
            current_user_data = users_collection.find_one({"staff_id": staff_id}) # Re-fetch to be absolutely sure
            if not current_user_data: return False, f"Staff member with ID {staff_id} not found."

            user_update_payload = {"$set": {}}
            auth_update_payload = {"$set": {}}
            
            for key, value in update_data.items():
                if key in ["name", "email", "departmentId", "isActive"]:
                    user_update_payload["$set"][key] = value
                if key == "roleName":
                    new_role_lower = value.lower()
                    user_update_payload["$set"][key] = new_role_lower
                    if staff_auth_collection: auth_update_payload["$set"]["role"] = new_role_lower
            
            if not user_update_payload["$set"] and (not auth_update_payload["$set"] or staff_auth_collection is None):
                 return True, "No changes to apply."


            user_modified_count, auth_modified_count = 0, 0
            result_user = None 
            auth_update_result = None 

            if user_update_payload["$set"]:
                result_user = users_collection.update_one({"staff_id": staff_id}, user_update_payload)
                user_modified_count = result_user.modified_count
                if result_user.matched_count == 0: return False, f"Staff member {staff_id} not found in users collection during update."
            
            if auth_update_payload["$set"] and staff_auth_collection is not None:
                # Ensure role in auth record is updated if roleName in user_profile changes
                if "role" in auth_update_payload["$set"]: # Only update if role change is part of payload
                    auth_update_result = staff_auth_collection.update_one({"staff_id": staff_id}, auth_update_payload)
                    if auth_update_result: # Check if result is not None
                        auth_modified_count = auth_update_result.modified_count
                        if not auth_update_result.matched_count: 
                            print(f"Warning: Role updated in users but no matching auth record found for staff ID {staff_id}.")
            elif auth_update_payload["$set"] and staff_auth_collection is None: print("Warning: staff_auth_collection is None, cannot update role in auth records.")


            if user_modified_count > 0 or auth_modified_count > 0: return True, f"Staff member {staff_id} updated successfully."
            elif (result_user and result_user.matched_count > 0 and user_modified_count == 0) or \
                 (auth_update_result and auth_update_result.matched_count > 0 and auth_modified_count == 0):
                 return True, "No effective changes made (values might be the same)."
            else: return False, f"Staff member {staff_id} not updated (or collections inaccessible)."
        except Exception as e: return False, f"Error updating staff member {staff_id}: {e}"

    def delete_staff_member(self, staff_id_to_delete, editor_profile=None, is_approved_action=False):
        if self.db is None: return False, "Database not connected."

        target_user_profile = self.get_user_profile(staff_id_to_delete)
        if not target_user_profile:
             return True, f"No staff member found with ID {staff_id_to_delete} (already deleted or never existed)."

        if editor_profile:
            editor_role = editor_profile.get("roleName","").lower()
            target_role = target_user_profile.get("roleName","").lower()
            
            if editor_role == "manager" and target_role == "developer":
                return False, "Managers cannot delete staff with the 'developer' role."
        
        if editor_profile and editor_profile.get("staff_id") == staff_id_to_delete:
            return False, "Users cannot delete their own account."


        users_collection = self.get_collection(self.users_collection_name)
        auth_collection = self.get_collection(self.staff_auth_collection_name)
        if users_collection is None or auth_collection is None: return False, "Could not retrieve necessary collections."
        try:
            user_delete_result = users_collection.delete_one({"staff_id": staff_id_to_delete})
            auth_delete_result = auth_collection.delete_one({"staff_id": staff_id_to_delete})
            deleted_count = user_delete_result.deleted_count + auth_delete_result.deleted_count
            if deleted_count > 0: return True, f"Successfully deleted records for staff ID: {staff_id_to_delete}."
            else: return False, f"Staff member {staff_id_to_delete} found but no records deleted (should not happen if profile existed)."
        except Exception as e: return False, f"Error deleting staff member {staff_id_to_delete}: {e}"

    def create_staff_action_request(self, requester_profile, action_type, target_staff_id, target_staff_name, details, proposed_changes=None):
        if self.db is None: return False, "Database not connected."
        requests_collection = self.get_collection(self.approval_requests_collection_name)
        if requests_collection is None: return False, "Approval requests collection not found."
        request_doc = {
            "request_id": str(uuid.uuid4()), "requester_staff_id": requester_profile.get("staff_id"),
            "requester_name": requester_profile.get("name"), "requester_role": requester_profile.get("roleName","").lower(),
            "action_type": action_type, "target_staff_id": target_staff_id, "target_staff_name": target_staff_name,
            "details": details, "proposed_changes": proposed_changes if proposed_changes else {}, "status": "pending",
            "requested_at_utc": datetime.datetime.now(pytz.utc), "processed_by_staff_id": None,
            "processed_by_name": None, "processed_at_utc": None, "manager_remarks": None
        }
        try:
            requests_collection.insert_one(request_doc)
            return True, f"Request for '{action_type.replace('_',' ').title()}' on staff {target_staff_name} (ID: {target_staff_id}) submitted."
        except Exception as e: return False, f"Error creating action request: {e}"

    def get_pending_action_requests(self):
        if self.db is None: return []
        requests_collection = self.get_collection(self.approval_requests_collection_name)
        if requests_collection is None: return []
        try: return list(requests_collection.find({"status": "pending"}).sort("requested_at_utc", 1))
        except Exception as e: print(f"Error fetching pending action requests: {e}"); return []

    def approve_action_request(self, request_id, approver_profile):
        if self.db is None: return False, "Database not connected."
        requests_collection = self.get_collection(self.approval_requests_collection_name)
        if requests_collection is None: return False, "Approval requests collection not found."
        try:
            result = requests_collection.update_one(
                {"request_id": request_id, "status": "pending"},
                {"$set": {"status": "approved", "processed_by_staff_id": approver_profile.get("staff_id"),
                          "processed_by_name": approver_profile.get("name"), "processed_at_utc": datetime.datetime.now(pytz.utc)}})
            if result.modified_count == 1: return True, f"Request {request_id} approved."
            return False, f"Request {request_id} not found or already processed."
        except Exception as e: return False, f"Error approving request: {e}"

    def decline_action_request(self, request_id, decliner_profile, remarks=""):
        if self.db is None: return False, "Database not connected."
        requests_collection = self.get_collection(self.approval_requests_collection_name)
        if requests_collection is None: return False, "Approval requests collection not found."
        try:
            result = requests_collection.update_one(
                {"request_id": request_id, "status": "pending"},
                {"$set": {"status": "declined", "processed_by_staff_id": decliner_profile.get("staff_id"),
                          "processed_by_name": decliner_profile.get("name"), "processed_at_utc": datetime.datetime.now(pytz.utc),
                          "manager_remarks": remarks}})
            if result.modified_count == 1: return True, f"Request {request_id} declined."
            return False, f"Request {request_id} not found or already processed."
        except Exception as e: return False, f"Error declining request: {e}"

    def update_staff_member_approved(self, staff_id_to_update, changes_to_apply, editor_profile=None):
        # This method is specifically for when an approval request leads to an update.
        # The editor_profile here would be the manager who approved.
        if self.db is None: return False, "Database not connected."
        # We can reuse update_staff_member, but crucial checks might differ or already be done.
        # For now, let's assume editor_profile is passed correctly.
        return self.update_staff_member(staff_id_to_update, changes_to_apply, editor_profile=editor_profile)


    def get_daily_sales(self, date_str, staff_id):
        if self.db is None: return None
        sales_collection = self.get_collection(self.daily_sales_collection_name)
        if sales_collection is not None:
            try:
                record = sales_collection.find_one({"date": date_str, "staff_id": staff_id})
                return record.get("totals") if record else None
            except Exception as e: print(f"Error getting daily sales for {staff_id} on {date_str}: {e}"); return None
        return None

    def save_daily_sales(self, date_str, staff_id, sales_totals):
        if self.db is None: return False
        sales_collection = self.get_collection(self.daily_sales_collection_name)
        if sales_collection is not None:
            try:
                query = {"date": date_str, "staff_id": staff_id}
                update = {"$set": {"totals": sales_totals, "last_updated": datetime.datetime.now(pytz.utc)}}
                sales_collection.update_one(query, update, upsert=True)
                return True
            except Exception as e: print(f"Error saving daily sales for {staff_id} on {date_str}: {e}"); return False
        return False

    def reset_daily_sales(self, date_str, staff_id):
        if self.db is None: return False
        sales_collection = self.get_collection(self.daily_sales_collection_name)
        if sales_collection is not None:
            try:
                zeroed_totals = {}
                sections = ["collected", "sold_cash", "sold_transfer", "sold_card", "returned", "damages"]
                item_keys = ["burger", "jumbo", "family", "short"]
                for section in sections: zeroed_totals[section] = {item: 0 for item in item_keys}
                query = {"date": date_str, "staff_id": staff_id}
                update = {"$set": {"totals": zeroed_totals, "last_updated": datetime.datetime.now(pytz.utc)}}
                sales_collection.update_one(query, update, upsert=True)
                return True
            except Exception as e: print(f"Error resetting daily sales for {staff_id} on {date_str}: {e}"); return False
        return False

    def send_notification(self, sender_staff_id, sender_name, sender_role, title, message, target_staff_ids=None):
        if self.db is None: return False
        notifications_collection = self.get_collection(self.notifications_collection_name)
        if notifications_collection is None: return False
        recipients = list(set(target_staff_ids)) if target_staff_ids else self.get_all_user_staff_ids()
        if not recipients: return False
        notification_doc = {
            "notification_id": str(uuid.uuid4()), "sender_staff_id": sender_staff_id, "sender_name": sender_name,
            "sender_role": sender_role.lower(), "title": title, "message": message, "recipient_staff_ids": recipients,
            "created_at_utc": datetime.datetime.now(pytz.utc), "is_global": (target_staff_ids is None or not target_staff_ids),
            "read_by_staff_ids": [], "cleared_by_user_ids": []
        }
        try:
            insert_result = notifications_collection.insert_one(notification_doc)
            return insert_result.inserted_id is not None
        except Exception as e: print(f"Error sending notification: {e}"); return False

    def get_notifications_for_staff(self, staff_id, limit=50):
        if self.db is None: return []
        notifications_collection = self.get_collection(self.notifications_collection_name)
        if notifications_collection is None: return []
        try:
            query = {"recipient_staff_ids": staff_id, "cleared_by_user_ids": {"$ne": staff_id}}
            notifications = list(notifications_collection.find(query).sort("created_at_utc", -1).limit(limit))
            for notif in notifications: notif['read'] = staff_id in notif.get('read_by_staff_ids', [])
            return notifications
        except Exception as e: print(f"Error fetching notifications for staff {staff_id}: {e}"); return []

    def clear_all_my_notifications_for_user(self, staff_id):
        if self.db is None: return False, "Database not connected."
        notifications_collection = self.get_collection(self.notifications_collection_name)
        if notifications_collection is None: return False, "Notifications collection not found."
        try:
            result = notifications_collection.update_many(
                {"recipient_staff_ids": staff_id, "cleared_by_user_ids": {"$ne": staff_id}},
                {"$addToSet": {"cleared_by_user_ids": staff_id}})
            return True, f"{result.modified_count} notifications cleared for staff {staff_id}."
        except Exception as e: return False, f"Error clearing notifications: {e}"

    def send_staff_report(self, reporter_staff_id, reporter_name, reporter_role, report_message): # General Staff
        if self.db is None: return False
        reports_collection = self.get_collection(self.staff_reports_collection_name)
        if reports_collection is None: return False
        report_doc = {
            "report_id": str(uuid.uuid4()), "reporter_staff_id": reporter_staff_id, "reporter_name": reporter_name,
            "reporter_role": reporter_role.lower(), "report_message": report_message, "report_category": "general_staff",
            "created_at_utc": datetime.datetime.now(pytz.utc), "status": "new"
        }
        try:
            insert_result = reports_collection.insert_one(report_doc)
            return insert_result.inserted_id is not None
        except Exception as e: print(f"Error sending staff report: {e}"); return False

    def send_cleaner_report(self, reporter_profile, report_message): # Cleaner-specific
        if self.db is None: return False, "Database connection failed."
        reports_collection = self.get_collection(self.cleaner_reports_collection_name)
        if reports_collection is None: return False, "Cleaner reports collection not found."
        report_doc = {
            "report_id": str(uuid.uuid4()),
            "reporter_staff_id": reporter_profile.get("staff_id"),
            "reporter_name": reporter_profile.get("name"),
            "reporter_role": reporter_profile.get("roleName","cleaner").lower(),
            "report_message": report_message,
            "report_category": "cleaner", # For easier filtering by management
            "created_at_utc": datetime.datetime.now(pytz.utc),
            "status": "new" 
        }
        try:
            reports_collection.insert_one(report_doc)
            return True, "Cleaner report submitted successfully."
        except Exception as e:
            print(f"Error sending cleaner report: {e}")
            return False, f"Error sending cleaner report: {e}"

    def send_baker_report(self, reporter_profile, report_message): # Baker-specific (textual)
        if self.db is None: return False, "Database connection failed."
        reports_collection = self.get_collection(self.baker_reports_collection_name)
        if reports_collection is None: return False, "Baker reports collection not found."
        report_doc = {
            "report_id": str(uuid.uuid4()),
            "reporter_staff_id": reporter_profile.get("staff_id"),
            "reporter_name": reporter_profile.get("name"),
            "reporter_role": reporter_profile.get("roleName","baker").lower(),
            "report_message": report_message,
            "report_category": "baker_textual", # Distinguish from production logs
            "created_at_utc": datetime.datetime.now(pytz.utc),
            "status": "new"
        }
        try:
            reports_collection.insert_one(report_doc)
            return True, "Baker report submitted successfully."
        except Exception as e:
            print(f"Error sending baker report: {e}")
            return False, f"Error sending baker report: {e}"

    def get_staff_reports(self, limit=100): # General Staff Reports
        if self.db is None: return []
        reports_collection = self.get_collection(self.staff_reports_collection_name)
        if reports_collection is None: return []
        try: return list(reports_collection.find({"report_category": "general_staff"}).sort("created_at_utc", -1).limit(limit))
        except Exception as e: print(f"Error fetching staff reports: {e}"); return []

    def get_cleaner_reports(self, limit=100):
        if self.db is None: return []
        reports_collection = self.get_collection(self.cleaner_reports_collection_name) # Use the correct collection
        if reports_collection is None: return []
        try: return list(reports_collection.find({"report_category": "cleaner"}).sort("created_at_utc", -1).limit(limit))
        except Exception as e: print(f"Error fetching cleaner reports: {e}"); return []

    def get_baker_reports(self, limit=100): # Textual reports from baker
        if self.db is None: return []
        reports_collection = self.get_collection(self.baker_reports_collection_name) # Use the correct collection
        if reports_collection is None: return []
        try: return list(reports_collection.find({"report_category": "baker_textual"}).sort("created_at_utc", -1).limit(limit))
        except Exception as e: print(f"Error fetching baker reports: {e}"); return []

    def get_reports_for_management(self, report_categories=None, limit_per_type=30):
        if self.db is None: return []
        all_reports = []
        
        # Default to all relevant categories if none specified
        if report_categories is None:
            report_categories = ["staff", "cleaner", "baker"] # Ensure these keys match category_map
            
        category_map = {
            "staff": (self.staff_reports_collection_name, "general_staff"),
            "cleaner": (self.cleaner_reports_collection_name, "cleaner"),
            "baker": (self.baker_reports_collection_name, "baker_textual") 
        }

        for cat_key in report_categories:
            if cat_key in category_map:
                coll_name, internal_cat_filter = category_map[cat_key]
                collection = self.get_collection(coll_name)
                # Corrected boolean check for the collection object
                if collection is not None: # <<< CORRECTION HERE
                    try:
                        reports = list(collection.find({"report_category": internal_cat_filter})
                                       .sort("created_at_utc", -1)
                                       .limit(limit_per_type))
                        all_reports.extend(reports)
                    except Exception as e:
                        print(f"Error fetching reports from {coll_name} for category '{internal_cat_filter}': {e}")
                else:
                    print(f"Warning: Collection '{coll_name}' not found for category '{cat_key}'.") # Added warning
        
        # Sort all collected reports by date, newest first
        all_reports.sort(key=lambda x: x.get("created_at_utc"), reverse=True)
        return all_reports

        if self.db is None: return []
        all_reports = []
        
        # Default to all relevant categories if none specified
        if report_categories is None:
            report_categories = ["staff", "cleaner", "baker"]
            
        category_map = {
            "staff": (self.staff_reports_collection_name, "general_staff"),
            "cleaner": (self.cleaner_reports_collection_name, "cleaner"),
            "baker": (self.baker_reports_collection_name, "baker_textual")
        }

        for cat_key in report_categories:
            if cat_key in category_map:
                coll_name, internal_cat_filter = category_map[cat_key]
                collection = self.get_collection(coll_name)
                if collection:
                    try:
                        reports = list(collection.find({"report_category": internal_cat_filter})
                                       .sort("created_at_utc", -1)
                                       .limit(limit_per_type))
                        all_reports.extend(reports)
                    except Exception as e:
                        print(f"Error fetching reports from {coll_name} for category '{internal_cat_filter}': {e}")
        
        # Sort all collected reports by date, newest first
        all_reports.sort(key=lambda x: x.get("created_at_utc"), reverse=True)
        # Apply a general limit if needed, or just return all fetched if limit_per_type is the main control
        # For simplicity, we assume limit_per_type is enough for now.
        return all_reports


    # --- Generic Inventory Helper Methods ---
    def _manage_inventory_item(self, collection_name, item_name, quantity, unit, user_profile, action="add"):
        if self.db is None: return False, "Database not connected."
        inventory_collection = self.get_collection(collection_name)
        if inventory_collection is None: return False, f"{collection_name} collection not found."

        if not item_name or quantity is None or not unit:
            return False, "Item name, quantity, and unit are required."
        try:
            quantity = int(quantity)
            if quantity < 0: return False, "Quantity cannot be negative."
        except ValueError: return False, "Quantity must be a valid number."

        item_doc_base = {
            "name": item_name, "name_lower": item_name.lower(), "quantity": quantity, "unit": unit,
            "last_updated_utc": datetime.datetime.now(pytz.utc),
            "updated_by_staff_id": user_profile.get("staff_id"), "updated_by_name": user_profile.get("name")
        }
        try:
            if action == "add":
                existing_item = inventory_collection.find_one({"name_lower": item_name.lower()})
                if existing_item:
                    return False, f"Item '{item_name}' already exists in {collection_name.replace('_',' ')}. Use update."
                item_doc = {"item_id": str(uuid.uuid4()), **item_doc_base}
                inventory_collection.insert_one(item_doc)
                return True, f"Item '{item_name}' added to {collection_name.replace('_',' ')}."
            return False, "Invalid action specified for _manage_inventory_item."
        except Exception as e: return False, f"Error managing item in {collection_name}: {e}"

    def _update_inventory_item_quantity(self, collection_name, item_id, new_quantity, user_profile):
        if self.db is None: return False, "Database not connected."
        inventory_collection = self.get_collection(collection_name)
        if inventory_collection is None: return False, f"{collection_name} collection not found."
        try: new_quantity = int(new_quantity)
        except ValueError: return False, "Quantity must be a valid number."
        if new_quantity < 0: return False, "Quantity cannot be negative."
        result = inventory_collection.update_one(
            {"item_id": item_id},
            {"$set": {"quantity": new_quantity, "last_updated_utc": datetime.datetime.now(pytz.utc),
                      "updated_by_staff_id": user_profile.get("staff_id"), "updated_by_name": user_profile.get("name")}})
        if result.matched_count == 0: return False, f"Item ID '{item_id}' not found in {collection_name.replace('_',' ')}."
        if result.modified_count == 1: return True, f"Item ID '{item_id}' quantity updated."
        return True, "Item quantity was already set to this value."

    def _remove_inventory_item(self, collection_name, item_id):
        if self.db is None: return False, "Database not connected."
        inventory_collection = self.get_collection(collection_name)
        if inventory_collection is None: return False, f"{collection_name} collection not found."
        result = inventory_collection.delete_one({"item_id": item_id})
        if result.deleted_count == 1: return True, f"Item ID '{item_id}' removed from {collection_name.replace('_',' ')}."
        return False, f"Item ID '{item_id}' not found."

    def _get_inventory_items(self, collection_name):
        if self.db is None: return []
        inventory_collection = self.get_collection(collection_name)
        if inventory_collection is None: return []
        try: return list(inventory_collection.find({}).sort("name_lower", 1))
        except Exception as e: print(f"Error fetching from {collection_name}: {e}"); return []

    # --- Cleaner Inventory Methods ---
    def add_cleaner_inventory_item(self, item_name, quantity, unit, added_by_profile):
        return self._manage_inventory_item(self.cleaner_inventory_collection_name, item_name, quantity, unit, added_by_profile, action="add")
    def update_cleaner_inventory_item_quantity(self, item_id, new_quantity, updated_by_profile):
        return self._update_inventory_item_quantity(self.cleaner_inventory_collection_name, item_id, new_quantity, updated_by_profile)
    def remove_cleaner_inventory_item(self, item_id):
        return self._remove_inventory_item(self.cleaner_inventory_collection_name, item_id)
    def get_cleaner_inventory(self):
        return self._get_inventory_items(self.cleaner_inventory_collection_name)

    # --- Baker Production Supplies Methods (Managed by Baker THEMSELVES or provisioned by manager and then Baker updates qty) ---
    # The 'added_by_profile' will determine who is making the change.
    def add_baker_supply_item(self, item_name, quantity, unit, added_by_profile):
        return self._manage_inventory_item(self.baker_supplies_collection_name, item_name, quantity, unit, added_by_profile, action="add")
    def update_baker_supply_item_quantity(self, item_id, new_quantity, updated_by_profile):
        return self._update_inventory_item_quantity(self.baker_supplies_collection_name, item_id, new_quantity, updated_by_profile)
    def remove_baker_supply_item(self, item_id): # Typically manager might remove, or baker if they fully manage it
        return self._remove_inventory_item(self.baker_supplies_collection_name, item_id)
    def get_baker_supplies(self):
        return self._get_inventory_items(self.baker_supplies_collection_name)

    # --- Storekeeper Supplies Methods ---
    def add_storekeeper_supply_item(self, item_name, quantity, unit, added_by_profile):
        return self._manage_inventory_item(self.storekeeper_supplies_collection_name, item_name, quantity, unit, added_by_profile, action="add")
    def update_storekeeper_supply_item_quantity(self, item_id, new_quantity, updated_by_profile):
        return self._update_inventory_item_quantity(self.storekeeper_supplies_collection_name, item_id, new_quantity, updated_by_profile)
    def remove_storekeeper_supply_item(self, item_id):
        return self._remove_inventory_item(self.storekeeper_supplies_collection_name, item_id)
    def get_storekeeper_supplies(self):
        return self._get_inventory_items(self.storekeeper_supplies_collection_name)


    # --- Baker Daily Production & Damages Log Methods ---
    def get_baker_daily_log(self, date_str, staff_id):
        if self.db is None: return None
        logs_collection = self.get_collection(self.baker_daily_logs_collection_name)
        if logs_collection is None: return None
        log_entry = logs_collection.find_one({"date": date_str, "staff_id": staff_id})
        item_keys = ["burger", "jumbo", "family", "short"]; default_structure = {item: 0 for item in item_keys}
        if log_entry: return {"production": log_entry.get("production", default_structure.copy()), "damages": log_entry.get("damages", default_structure.copy())}
        return {"production": default_structure.copy(), "damages": default_structure.copy()}

    def save_baker_daily_log(self, date_str, staff_id, production_additions, damages_additions):
        if self.db is None: return False, "Database not connected."
        logs_collection = self.get_collection(self.baker_daily_logs_collection_name)
        if logs_collection is None: return False, "Baker daily logs collection not found."
        current_log_data = self.get_baker_daily_log(date_str, staff_id)
        new_production_totals = current_log_data.get("production", {}).copy()
        new_damages_totals = current_log_data.get("damages", {}).copy()
        item_keys = ["burger", "jumbo", "family", "short"]
        for item_key in item_keys:
            new_production_totals[item_key] = new_production_totals.get(item_key, 0) + production_additions.get(item_key, 0)
            new_damages_totals[item_key] = new_damages_totals.get(item_key, 0) + damages_additions.get(item_key, 0)
        try:
            logs_collection.update_one(
                {"date": date_str, "staff_id": staff_id},
                {"$set": {"production": new_production_totals, "damages": new_damages_totals, "last_updated_utc": datetime.datetime.now(pytz.utc)}}, upsert=True)
            return True, "Baker daily log saved."
        except Exception as e: return False, f"Error saving baker daily log: {e}"

    def reset_baker_daily_log(self, date_str, staff_id):
        if self.db is None: return False, "Database not connected."
        logs_collection = self.get_collection(self.baker_daily_logs_collection_name)
        if logs_collection is None: return False, "Baker daily logs collection not found."
        item_keys = ["burger", "jumbo", "family", "short"]; zeroed_data = {item: 0 for item in item_keys}
        try:
            logs_collection.update_one(
                {"date": date_str, "staff_id": staff_id},
                {"$set": {"production": zeroed_data, "damages": zeroed_data, "last_updated_utc": datetime.datetime.now(pytz.utc)}}, upsert=True)
            return True, "Baker daily log reset."
        except Exception as e: return False, f"Error resetting baker log: {e}"

    # --- Aggregated Data Methods ---
    def get_staff_sales_summary_for_period(self, start_date, end_date, staff_id_filter=None):
        if self.db is None: return []
        sales_collection = self.get_collection(self.daily_sales_collection_name)
        if sales_collection is None: return []
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        match_conditions = {"date": {"$gte": start_date_str, "$lte": end_date_str}}
        if staff_id_filter and staff_id_filter.lower() != "all" and staff_id_filter.lower() != "all staff":
            match_conditions["staff_id"] = staff_id_filter
            
        pipeline = [ {"$match": match_conditions} ]
        # Ensure totals paths are correct
        pipeline.extend([
            {"$project": {
                "b_coll": {"$ifNull": ["$totals.collected.burger", 0]}, "j_coll": {"$ifNull": ["$totals.collected.jumbo", 0]}, "f_coll": {"$ifNull": ["$totals.collected.family", 0]}, "s_coll": {"$ifNull": ["$totals.collected.short", 0]},
                "b_cash": {"$ifNull": ["$totals.sold_cash.burger", 0]}, "j_cash": {"$ifNull": ["$totals.sold_cash.jumbo", 0]}, "f_cash": {"$ifNull": ["$totals.sold_cash.family", 0]}, "s_cash": {"$ifNull": ["$totals.sold_cash.short", 0]},
                "b_tran": {"$ifNull": ["$totals.sold_transfer.burger", 0]}, "j_tran": {"$ifNull": ["$totals.sold_transfer.jumbo", 0]}, "f_tran": {"$ifNull": ["$totals.sold_transfer.family", 0]}, "s_tran": {"$ifNull": ["$totals.sold_transfer.short", 0]},
                "b_card": {"$ifNull": ["$totals.sold_card.burger", 0]}, "j_card": {"$ifNull": ["$totals.sold_card.jumbo", 0]}, "f_card": {"$ifNull": ["$totals.sold_card.family", 0]}, "s_card": {"$ifNull": ["$totals.sold_card.short", 0]},
                "b_ret": {"$ifNull": ["$totals.returned.burger", 0]}, "j_ret": {"$ifNull": ["$totals.returned.jumbo", 0]}, "f_ret": {"$ifNull": ["$totals.returned.family", 0]}, "s_ret": {"$ifNull": ["$totals.returned.short", 0]},
                "b_dmg": {"$ifNull": ["$totals.damages.burger", 0]}, "j_dmg": {"$ifNull": ["$totals.damages.jumbo", 0]}, "f_dmg": {"$ifNull": ["$totals.damages.family", 0]}, "s_dmg": {"$ifNull": ["$totals.damages.short", 0]},
                "_id": 0 }},
            {"$group": {
                "_id": None,
                "t_b_coll": {"$sum": "$b_coll"}, "t_j_coll": {"$sum": "$j_coll"}, "t_f_coll": {"$sum": "$f_coll"}, "t_s_coll": {"$sum": "$s_coll"},
                "t_b_cash": {"$sum": "$b_cash"}, "t_j_cash": {"$sum": "$j_cash"}, "t_f_cash": {"$sum": "$f_cash"}, "t_s_cash": {"$sum": "$s_cash"},
                "t_b_tran": {"$sum": "$b_tran"}, "t_j_tran": {"$sum": "$j_tran"}, "t_f_tran": {"$sum": "$f_tran"}, "t_s_tran": {"$sum": "$s_tran"},
                "t_b_card": {"$sum": "$b_card"}, "t_j_card": {"$sum": "$j_card"}, "t_f_card": {"$sum": "$f_card"}, "t_s_card": {"$sum": "$s_card"},
                "t_b_ret": {"$sum": "$b_ret"}, "t_j_ret": {"$sum": "$j_ret"}, "t_f_ret": {"$sum": "$f_ret"}, "t_s_ret": {"$sum": "$s_ret"},
                "t_b_dmg": {"$sum": "$b_dmg"}, "t_j_dmg": {"$sum": "$j_dmg"}, "t_f_dmg": {"$sum": "$f_dmg"}, "t_s_dmg": {"$sum": "$s_dmg"},
            }}])
        try:
            result = list(sales_collection.aggregate(pipeline))
            if not result or result[0].get('_id') is None : return [] # Check if group stage produced results
            aggregated_data = result[0]; report_lines = []
            item_types = [("burger", "b"), ("jumbo", "j"), ("family", "f"), ("short", "s")]
            for item_title, item_prefix in item_types:
                report_lines.append({
                    "item": item_title.title(),
                    "collected": aggregated_data.get(f"t_{item_prefix}_coll", 0), "sold_cash": aggregated_data.get(f"t_{item_prefix}_cash", 0),
                    "sold_transfer": aggregated_data.get(f"t_{item_prefix}_tran", 0), "sold_card": aggregated_data.get(f"t_{item_prefix}_card", 0),
                    "returned": aggregated_data.get(f"t_{item_prefix}_ret", 0), "damages": aggregated_data.get(f"t_{item_prefix}_dmg", 0),})
            return report_lines
        except Exception as e: print(f"Error aggregating sales summary (filter: {staff_id_filter}): {e}"); return []


    def get_aggregated_baker_production_for_period(self, start_date, end_date):
        if self.db is None: return []
        logs_collection = self.get_collection(self.baker_daily_logs_collection_name);
        if logs_collection is None: return []
        start_date_str = start_date.strftime("%Y-%m-%d"); end_date_str = end_date.strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"date": {"$gte": start_date_str, "$lte": end_date_str}}},
            {"$project": {
                "b_prod": {"$ifNull": ["$production.burger", 0]}, 
                "j_prod": {"$ifNull": ["$production.jumbo", 0]}, 
                "f_prod": {"$ifNull": ["$production.family", 0]}, 
                "s_prod": {"$ifNull": ["$production.short", 0]}, 
                "_id": 0
            }},
            {"$group": {"_id": None, "t_b_prod": {"$sum": "$b_prod"}, "t_j_prod": {"$sum": "$j_prod"}, "t_f_prod": {"$sum": "$f_prod"}, "t_s_prod": {"$sum": "$s_prod"}}}
        ]
        try:
            result = list(logs_collection.aggregate(pipeline));
            if not result or result[0].get('_id') is None: return []
            aggregated_data = result[0]; report_lines = []
            item_types = [("burger", "b"), ("jumbo", "j"), ("family", "f"), ("short", "s")]
            for item_title, item_prefix in item_types: report_lines.append({"bread_type": item_title.title(), "produced": aggregated_data.get(f"t_{item_prefix}_prod", 0)})
            return report_lines
        except Exception as e: print(f"Error aggregating baker production: {e}"); return []

    def get_aggregated_baker_damages_for_period(self, start_date, end_date):
        if self.db is None: return []
        logs_collection = self.get_collection(self.baker_daily_logs_collection_name)
        if logs_collection is None: return []
        start_date_str = start_date.strftime("%Y-%m-%d"); end_date_str = end_date.strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"date": {"$gte": start_date_str, "$lte": end_date_str}}},
            {"$project": {
                "b_dmg": {"$ifNull": ["$damages.burger", 0]}, 
                "j_dmg": {"$ifNull": ["$damages.jumbo", 0]}, 
                "f_dmg": {"$ifNull": ["$damages.family", 0]}, 
                "s_dmg": {"$ifNull": ["$damages.short", 0]}, 
                "_id": 0
            }},
            {"$group": {"_id": None, "t_b_dmg": {"$sum": "$b_dmg"}, "t_j_dmg": {"$sum": "$j_dmg"}, "t_f_dmg": {"$sum": "$f_dmg"}, "t_s_dmg": {"$sum": "$s_dmg"}}}
        ]
        try:
            result = list(logs_collection.aggregate(pipeline))
            if not result or result[0].get('_id') is None: return []
            aggregated_data = result[0]; report_lines = []
            item_types = [("burger", "b"), ("jumbo", "j"), ("family", "f"), ("short", "s")]
            for item_title, item_prefix in item_types: report_lines.append({"bread_type": item_title.title(), "damaged": aggregated_data.get(f"t_{item_prefix}_dmg", 0)})
            return report_lines
        except Exception as e: print(f"Error aggregating baker damages: {e}"); return []


if __name__ == "__main__":
    db_handler = DBHandler()
    if db_handler.client is not None and db_handler.db is not None:
        print("\n--- Populating Initial Data (if needed) ---")
        # For a clean run, uncomment the following to clear data:
        # print("Clearing existing data...")
        # collections_to_clear = [
        #     db_handler.users_collection_name, db_handler.staff_auth_collection_name,
        #     db_handler.daily_sales_collection_name, db_handler.notifications_collection_name,
        #     db_handler.staff_reports_collection_name, db_handler.approval_requests_collection_name,
        #     db_handler.cleaner_inventory_collection_name, db_handler.baker_supplies_collection_name,
        #     db_handler.baker_daily_logs_collection_name, db_handler.storekeeper_supplies_collection_name,
        #     db_handler.cleaner_reports_collection_name, db_handler.baker_reports_collection_name
        # ]
        # for coll_name in collections_to_clear:
        #     db_handler.db[coll_name].delete_many({})
        # print("Existing data cleared.")

        print("\n--- Setting up initial staff accounts (if they don't exist) ---")
        dev_profile_check = db_handler.get_user_profile("000000") # Developer
        manager_profile_check = db_handler.get_user_profile("100001") # Manager
        
        if not dev_profile_check:
            db_handler.initial_staff_setup("000000", "DevPassword1!", "Gabriel Developer", "gabriel.dev@example.com", "developer", "TECH_DEPT")
        if not manager_profile_check:
             db_handler.initial_staff_setup("100001", "ManagerPass1!", "Chris Manager", "chris.mgr@example.com", "manager", "GENERAL_MGMT")
        
        dev_profile = db_handler.get_user_profile("000000") # Used by developer to add other users
        manager_profile = db_handler.get_user_profile("100001") # Used by manager to add other users

        # Setup other staff only if the manager (who would typically add them) exists
        if manager_profile:
            if not db_handler.get_user_profile("200002"): # Check for one staff to prevent re-running if partially setup
                db_handler.initial_staff_setup("200002", "SupervisorPass1!", "Vic Supervisor", "vic.sup@example.com", "supervisor", "OPERATIONS_LEAD", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("300003", "AccountantPass1!", "Favour Accountant", "favour.acc@example.com", "accountant", "FINANCE_DEPT", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("400004", "StaffPass1!", "Mfon Staff", "mfon.staff@example.com", "staff", "OPERATIONS", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("400005", "StaffPass2!", "Akan Staff Inactive", "akan.staff@example.com", "staff", "OPERATIONS", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("500006", "BakerPass1!", "Blessing Baker", "blessing.baker@example.com", "baker", "KITCHEN_DEPT", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("600007", "CleanerPass1!", "John Cleaner", "john.cleaner@example.com", "cleaner", "FACILITIES_DEPT", added_by_profile=manager_profile)
                db_handler.initial_staff_setup("700008", "StorekeeperPass1!", "David Storekeeper", "david.store@example.com", "storekeeper", "LOGISTICS_DEPT", added_by_profile=manager_profile)
                
                # Make one staff inactive for testing
                if db_handler.get_user_profile("400005"): # Ensure Akan exists before trying to update
                    db_handler.update_staff_member("400005", {"isActive": False}, editor_profile=manager_profile)
                print("Initial staff accounts set up.")
            else:
                print("Other staff accounts seem to exist. Assuming initial setup was done.")
        else:
            print("Manager account '100001' not found. Skipping setup of other staff roles.")


        print("\n--- Setting up initial cleaner inventory (if empty) ---")
        cleaner_profile = db_handler.get_user_profile("600007")
        if cleaner_profile and not db_handler.get_cleaner_inventory():
            db_handler.add_cleaner_inventory_item("Floor Soap", 10, "Bottles", cleaner_profile)
            db_handler.add_cleaner_inventory_item("Hand Wash", 5, "Bottles", cleaner_profile)
            db_handler.add_cleaner_inventory_item("Air Freshener", 3, "Cans", cleaner_profile)
            print("Cleaner inventory populated.")

        print("\n--- Setting up initial baker production supplies (by Manager, if empty) ---")
        # Manager provisions initial supplies for the baker
        if manager_profile and not db_handler.get_baker_supplies():
            db_handler.add_baker_supply_item("Flour", 50, "KG", manager_profile) # Manager is 'added_by_profile'
            db_handler.add_baker_supply_item("Sugar", 20, "KG", manager_profile)
            db_handler.add_baker_supply_item("Yeast", 5, "Packs", manager_profile)
            db_handler.add_baker_supply_item("Salt", 2, "KG", manager_profile)
            print("Baker production supplies populated by Manager.")

        print("\n--- Setting up initial storekeeper supplies (by Storekeeper, if empty) ---")
        storekeeper_profile = db_handler.get_user_profile("700008")
        if storekeeper_profile and not db_handler.get_storekeeper_supplies():
            db_handler.add_storekeeper_supply_item("Rice Bags", 100, "Bags (50kg)", storekeeper_profile)
            db_handler.add_storekeeper_supply_item("Oil Cans", 20, "Cans (25L)", storekeeper_profile)
            db_handler.add_storekeeper_supply_item("Packaging Boxes", 500, "Units", storekeeper_profile)
            db_handler.add_storekeeper_supply_item("Disposable Plates", 1000, "Packs of 50", storekeeper_profile)
            print("Storekeeper supplies populated.")
        
        print("\n--- Adding Sample Reports (if none exist) ---")
        baker_profile = db_handler.get_user_profile("500006")
        if baker_profile and not db_handler.get_baker_reports():
            db_handler.send_baker_report(baker_profile, "Oven temperature seems inconsistent. Needs checking.")
            print("Added sample baker report.")
        
        if cleaner_profile and not db_handler.get_cleaner_reports():
            db_handler.send_cleaner_report(cleaner_profile, "Ran out of window cleaning spray. Please restock.")
            print("Added sample cleaner report.")

        general_staff_profile = db_handler.get_user_profile("400004")
        if general_staff_profile and not db_handler.get_staff_reports():
             db_handler.send_staff_report(general_staff_profile.get("staff_id"), general_staff_profile.get("name"), general_staff_profile.get("roleName"), "Customer POS machine is malfunctioning frequently.")
             print("Added sample general staff report.")


        db_handler.close_connection()
    else:
        print("Could not connect to DB to populate initial data or run tests.")