
## Membership
### Register
    $ curl http://${IP}/apiv1/clients -X REGISTER -d"email=cientx@test.com" -d"password=123456"

### Login
    $ curl http://${IP}/apiv1/sessions -X POST -d"email=client1@test.com" -d"password=123456"

### Get profile
    $ curl http://${IP}/apiv1/clients/me -X GET -H"Authorization: $TOKEN"

### Schedule verification email
    $ curl http://${IP}/apiv1/clients/email-verifications -X SCHEDULE -H"Authorization: $TOKEN"

### Verify verification email
    $ curl http://${IP}/apiv1/clients/email-verifications -X VERIFY -d"token=$EMAIL_TOKEN" -H"Authorization: $TOKEN"

### Schedule mobile phone verification
    $ curl http://${IP}/apiv1/clients/mobile-phone-verifications -X SCHEDULE -d"phone=%2B11111111" -H"Authorization: $TOKEN"

### Verify mobile phone verification
    $ curl http://${IP}/apiv1/clients/mobile-phone-verifications -X VERIFY -d"phone=%2B11111111" -d"code=111111" -H"Authorization: $TOKEN"

### Schedule fixed phone verification
    $ curl http://${IP}/apiv1/clients/fixed-phone-verifications -X SCHEDULE -d"phone=%2B11111111" -H"Authorization: $TOKEN"

### Verify fixed phone verification
    $ curl http://${IP}/apiv1/clients/fixed-phone-verifications -X VERIFY -d"phone=%2B11111111" -d"code=111111" -H"Authorization: $TOKEN"
