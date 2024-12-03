# Install PaytmChecksum module before using this script
# pip install paytmchecksum

from paytmchecksum import PaytmChecksum

def generate_checksum(param_dict, secret_key):
    """
    Generate checksum for Paytm parameters.
    :param param_dict: Dictionary of Paytm parameters
    :param secret_key: Paytm Merchant Key
    :return: Generated checksum
    """
    return PaytmChecksum.generateSignature(param_dict, secret_key)

def verify_checksum(param_dict, secret_key, checksum_hash):
    """
    Verify checksum for Paytm parameters.
    :param param_dict: Dictionary of Paytm parameters
    :param secret_key: Paytm Merchant Key
    :param checksum_hash: The checksum hash to verify
    :return: Boolean indicating whether checksum is valid
    """
    return PaytmChecksum.verifySignature(param_dict, secret_key, checksum_hash)


# Example usage:
if __name__ == "__main__":
    # Replace with your actual parameters and keys
    params = {
        "MID": "YourMerchantID",
        "ORDER_ID": "Order12345",
        "CUST_ID": "Customer001",
        "TXN_AMOUNT": "100",
        "CHANNEL_ID": "WEB",
        "WEBSITE": "WEBSTAGING",  # Use "WEBSTAGING" for testing
        "INDUSTRY_TYPE_ID": "Retail"
    }

    merchant_key = "YourMerchantKey"

    # Generate checksum
    checksum = generate_checksum(params, merchant_key)
    print("Generated Checksum:", checksum)

    # Verify checksum (example scenario with received checksum from Paytm response)
    received_checksum = checksum  # For testing, use the same checksum generated above
    is_valid = verify_checksum(params, merchant_key, received_checksum)
    print("Is Checksum Valid:", is_valid)
