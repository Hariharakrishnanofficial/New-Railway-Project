import logging
from flask import Request, make_response, jsonify
import zcatalyst_sdk

def handler(request: Request):
    app = zcatalyst_sdk.initialize()
    logger = logging.getLogger()
    path = request.path
    method = request.method

    try:
        # CREATE TODO/USER RECORD
        if path == "/items" and method == "POST":
            req_data = request.get_json()

            # Handle all database fields
            todo_data = {
                'Full-Name': req_data.get('fullName', ''),
                'Password': req_data.get('password', ''),
                'Role': req_data.get('role', ''),
                'Account_Status': req_data.get('accountStatus', 'Active'),
                'Aadhar_Verified': req_data.get('aadharVerified', False),
                'ID_Proof_Type': req_data.get('idProofType', ''),
                'Address': req_data.get('address', ''),
                'Image': req_data.get('image', ''),
                'item-name': req_data.get('title', ''),
                'status': req_data.get('status', 'pending')
            }

            try:
                table = app.datastore().table('TodoItems')
                row = table.insert_row(todo_data)

                # Return all fields in response
                todo_item = {
                    'id': row['ROWID'],
                    'fullName': row.get('Full-Name'),
                    'password': row.get('Password'),
                    'role': row.get('Role'),
                    'accountStatus': row.get('Account_Status'),
                    'aadharVerified': row.get('Aadhar_Verified'),
                    'idProofType': row.get('ID_Proof_Type'),
                    'address': row.get('Address'),
                    'image': row.get('Image'),
                    'title': row.get('item-name'),
                    'status': row.get('status')
                }
                return make_response(jsonify({'status': 'success', 'data': {'todoItem': todo_item}}), 201)
            except Exception as e:
                logger.error(f"Failed to insert record: {e}")
                return make_response(jsonify({
                    'status': 'error',
                    'message': f'Database error: {str(e)}'
                }), 500)

        # GET ALL RECORDS
        elif path == "/items" and method == "GET":
            try:
                zcql_service = app.zcql()
                query_result = zcql_service.execute_query(
                    'SELECT ROWID, `Full-Name`, Password, Role, Account_Status, Aadhar_Verified, ID_Proof_Type, Address, Image, `item-name`, status FROM TodoItems ORDER BY ROWID DESC'
                )

                todo_items = []
                for item in query_result:
                    row = item['TodoItems']
                    todo_items.append({
                        'id': row['ROWID'],
                        'fullName': row.get('Full-Name', ''),
                        'password': row.get('Password', ''),
                        'role': row.get('Role', ''),
                        'accountStatus': row.get('Account_Status', ''),
                        'aadharVerified': row.get('Aadhar_Verified', ''),
                        'idProofType': row.get('ID_Proof_Type', ''),
                        'address': row.get('Address', ''),
                        'image': row.get('Image', ''),
                        'title': row.get('item-name', ''),
                        'status': row.get('status', '')
                    })
                return make_response(jsonify({'status': 'success', 'data': {'todoItems': todo_items}}), 200)
            except Exception as e:
                logger.warning(f"Database query error: {e}")
                return make_response(jsonify({
                    'status': 'error',
                    'data': {'todoItems': []},
                    'message': f'Database error: {str(e)}'
                }), 500)

        # GET ONE RECORD
        elif path.startswith("/items/") and method == "GET":
            row_id = path.split("/items/")[-1]
            try:
                table = app.datastore().table('TodoItems')
                row = table.get_row(row_id)
                if row:
                    todo_item = {
                        'id': row['ROWID'],
                        'fullName': row.get('Full-Name', ''),
                        'password': row.get('Password', ''),
                        'role': row.get('Role', ''),
                        'accountStatus': row.get('Account_Status', ''),
                        'aadharVerified': row.get('Aadhar_Verified', ''),
                        'idProofType': row.get('ID-Proof_Type', ''),
                        'address': row.get('Address', ''),
                        'image': row.get('Image', ''),
                        'title': row.get('item-name', ''),
                        'status': row.get('status', '')
                    }
                    return make_response(jsonify({'status': 'success', 'data': {'todoItem': todo_item}}), 200)
                else:
                    return make_response(jsonify({'status': 'failure', 'error': 'Item not found'}), 404)
            except Exception as e:
                return make_response(jsonify({'status': 'failure', 'error': f'Database error: {str(e)}'}), 404)

        # UPDATE RECORD
        elif path.startswith("/items/") and method == "PUT":
            row_id = path.split("/items/")[-1]
            req_data = request.get_json()

            update_data = {
                'ROWID': row_id,
                'Full-Name': req_data.get('fullName', ''),
                'Password': req_data.get('password', ''),
                'Role': req_data.get('role', ''),
                'Account_Status': req_data.get('accountStatus', ''),
                'Aadhar_Verified': req_data.get('aadharVerified', False),
                'ID_Proof_Type': req_data.get('idProofType', ''),
                'Address': req_data.get('address', ''),
                'Image': req_data.get('image', ''),
                'item-name': req_data.get('title', ''),
                'status': req_data.get('status', '')
            }

            try:
                table = app.datastore().table('TodoItems')
                updated_row = table.update_row(update_data)
                todo_item = {
                    'id': updated_row['ROWID'],
                    'fullName': updated_row.get('Full-Name', ''),
                    'password': updated_row.get('Password', ''),
                    'role': updated_row.get('Role', ''),
                    'accountStatus': updated_row.get('Account_Status', ''),
                    'aadharVerified': updated_row.get('Aadhar_Verified', ''),
                    'idProofType': updated_row.get('ID-Proof_Type', ''),
                    'address': updated_row.get('Address', ''),
                    'image': updated_row.get('Image', ''),
                    'title': updated_row.get('item-name', ''),
                    'status': updated_row.get('status', '')
                }
                return make_response(jsonify({'status': 'success', 'data': {'todoItem': todo_item}}), 200)
            except Exception as e:
                logger.error(f"Failed to update record: {e}")
                return make_response(jsonify({'status': 'failure', 'error': f'Update failed: {str(e)}'}), 500)

        # DELETE RECORD
        elif path.startswith("/items/") and method == "DELETE":
            row_id = path.split("/items/")[-1]
            try:
                table = app.datastore().table('TodoItems')
                table.delete_row(row_id)
                return make_response(jsonify({'status': 'success', 'data': {'todoItem': {'id': row_id}}}), 200)
            except Exception as e:
                logger.error(f"Failed to delete record: {e}")
                return make_response(jsonify({'status': 'failure', 'error': f'Delete failed: {str(e)}'}), 500)

        else:
            return make_response(jsonify({'status': 'failure', 'error': 'Unknown path or method'}), 400)

    except Exception as err:
        logger.error(f"Exception in TodoItems CRUD: {err}")
        return make_response(jsonify({"error": "Internal server error occurred. Please try again later."}), 500)