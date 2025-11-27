import boto3
import json
from botocore.exceptions import ClientError
import base64
from functools import lru_cache


class ItemManager:
    def __init__(self, list_name, user_name):
        self.list_name = list_name
        self.user_name = user_name
        self.lambda_client = boto3.client('lambda')
        self.kms_client = boto3.client('kms', region_name='eu-north-1')
        self._cache = None  # Cache to store items

    def encrypt_data(self, data):
        """Encrypt data using AWS KMS."""
        try:
            response = self.kms_client.encrypt(
                KeyId='alias/MyEncryptionKey',
                Plaintext=data.encode('utf-8')
            )
            return base64.b64encode(response['CiphertextBlob']).decode('utf-8')  # Encode as Base64
        except ClientError as e:
            print(f"Encryption error: {e}")
            raise

    def decrypt_data(self, encrypted_data):
        """Decrypt data using AWS KMS."""
        try:
            # Decode the Base64-encoded encrypted data
            encrypted_bytes = base64.b64decode(encrypted_data)
            response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_bytes
            )
            return response['Plaintext'].decode('utf-8')
        except ClientError as e:
            print(f"Decryption error: {e}")
            raise

    def call_lambda(self, function_name, payload):
        """Call AWS Lambda and handle encryption/decryption."""
        # Encrypt only the 'amount' field in the payload before sending to Lambda
        if 'item' in payload:
            item = payload['item']
            if 'amount' in item and item['amount']:
                item['amount'] = self.encrypt_data(str(item['amount']))
            payload['item'] = item

        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response['Payload'].read().decode())

        # Decrypt only the 'amount' field in the response if needed
        if 'body' in response_payload:
            body = json.loads(response_payload['body'])
            if isinstance(body, list):
                decrypted_items = [self.decrypt_item(item) for item in body]  # Sequential decryption
                response_payload['body'] = json.dumps(decrypted_items)

        return response_payload

    def decrypt_item(self, item):
        """Decrypt only the 'amount' field in a single item."""
        if 'amount' in item and item['amount']:
            item['amount'] = self.decrypt_data(item['amount'])
        return item

    def call_lambda_remove(self, function_name, payload):
        """Call AWS Lambda and handle encryption/decryption for remove_item_by_name."""
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            response_payload = json.loads(response['Payload'].read().decode())
            return response_payload
        except Exception as e:
            print(f"Error invoking Lambda function: {e}")
            raise

    def get_items(self):
        """Retrieve and decrypt the items from the list."""
        if self._cache is not None:
            return self._cache  # Return cached items if available

        payload = {
            "user_name": self.user_name,
            "list_name": self.list_name
        }

        # Call the Lambda function to get the encrypted items
        response = self.call_lambda('Get_Items', payload)

        # Decrypt the items before returning them
        encrypted_items = json.loads(response['body'])
        self._cache = encrypted_items  # Cache the items
        return encrypted_items

    def add_item(self, name, amount=None, expiration_date=None, entry_date=None):
        item = {
            "name": name,
            "amount": amount,
            "expiration_date": expiration_date,
            "entry_date": entry_date
        }
        payload = {
            "user_name": self.user_name,
            "list_name": self.list_name,
            "item": item
        }

        # Call the Lambda function to add the item
        response = self.call_lambda('Add_Item', payload)

        # Invalidate the cache to reflect the new item
        self._cache = None

        return response

    def remove_item_by_name(self, name):
        payload = {
            "user_name": self.user_name,
            "list_name": self.list_name,
            "item": {
                "name": name  # No need to encrypt the name
            }
        }

        # Call the Lambda function to remove the item
        response = self.call_lambda_remove('Remove_Item', payload)

        # Invalidate the cache to reflect the removed item
        self._cache = None

        return response

    def update_item(self, name, new_amount):
        items = self.get_items()
        for index, item in enumerate(items):
            if item['name'] == name:
                # Create a copy of the item and update the amount
                updated_item = item.copy()
                updated_item['amount'] = self.encrypt_data(str(new_amount))  # Encrypt the new amount

                # Prepare the payload
                payload = {
                    "user_name": self.user_name,
                    "list_name": self.list_name,
                    "item_index": index,
                    "updated_item": updated_item
                }

                # Call the Lambda function to update the item
                response = self.call_lambda('Update_Item', payload)

                # Invalidate the cache to reflect the updated item
                self._cache = None

                return response

    def has_item(self, name):
        payload = {
            "user_name": self.user_name,
            "list_name": self.list_name,
            "item_name": name  # No need to encrypt the name
        }

        # Call the Lambda function to check if the item exists
        response = self.call_lambda('Check_Item_Existence', payload)
        return json.loads(response['body'])

    def get_item_amount(self, name):
        """
        Get the amount of a specific item in the list.

        Args:
            name (str): The name of the item to search for.

        Returns:
            str: The amount of the item if found, otherwise None.
        """
        # Get all items in the list
        items = self.get_items()

        # Search for the item by name (case-insensitive comparison)
        for item in items:
            if item['name'].lower() == name.lower():  # Case-insensitive comparison
                return item['amount']

        # If the item is not found, return None
        return None

class DefaultListManager:
    def __init__(self, user_name):
        self.user_name = user_name
        self.lambda_client = boto3.client('lambda')

    def call_lambda(self, function_name, payload):
        """Call AWS Lambda."""
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response['Payload'].read().decode())
        return response_payload

    def get_items(self):
        """Retrieve the default list items."""
        payload = {
            "user_name": self.user_name
        }
        response = self.call_lambda('Get_Default_Items', payload)

        # Check if the response contains an error
        if "error" in response:
            print("Error:", response["error"])
            return []  # Return an empty list or handle the error as needed

        # Get the items from the response
        items = json.loads(response['body'])
        return items

    def add_item(self, item_name):
        """Add an item to the default list."""
        try:
            # Prepare the payload for the Lambda function
            payload = {
                "user_name": self.user_name,
                "item_name": item_name  # No encryption needed for item name
            }

            # Call the Lambda function
            response = self.call_lambda('Add_Item_To_Default_List', payload)

            return response
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

    def remove_item(self, item_name):
        """Remove an item from the default list."""
        try:
            # Prepare the payload for the Lambda function
            payload = {
                "user_name": self.user_name,
                "item_name": item_name  # No encryption needed for item name
            }

            # Call the Lambda function
            response = self.call_lambda('Remove_Item_From_Default_List', payload)

            return response
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

class Expired(ItemManager):
    def __init__(self, list_name="expired_list", user_name=None):
        super().__init__(list_name, user_name)


class ExpiringSoon(ItemManager):
    def __init__(self, list_name="expiring_soon_list", user_name=None):
        super().__init__(list_name, user_name)


class InStock(ItemManager):
    def __init__(self, list_name="in_stock_list", user_name=None):
        super().__init__(list_name, user_name)


class Shopping(ItemManager):
    def __init__(self, list_name="shopping_list", user_name=None):
        super().__init__(list_name, user_name)


class DefaultList(DefaultListManager):
    def __init__(self, user_name=None):
        super().__init__(user_name)