-- disable eagle payment provider
UPDATE payment_provider
   SET eagle_public_key = NULL,
       eagle_api_key = NULL,
       eagle_client_id = NULL;
