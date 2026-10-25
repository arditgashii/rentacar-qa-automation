# Test cases

Every automated test has its test case here. Expected results describe the correct product; four of
them fail on purpose while DriveNow runs with its [intentional bugs](https://github.com/arditgashii/rentacar-platform/blob/main/docs/INTENTIONAL-BUGS.md).

| ID | Title | Type | Markers | With `DRIVENOW_BUGS=on` |
|---|---|---|---|---|
| TC-001 | Admin logs in and sees the dashboard stats | UI | smoke, ui, admin | pass |
| TC-002 | Login with a wrong password shows an error and no session | UI | smoke, ui, no_login | pass |
| TC-003 | A new client registers through the API and can log in, an inactive user cannot | API | smoke, api, no_login | pass |
| TC-004 | Client creates a listing with 3 photos; the photos are in Blob Storage and the first is primary | UI + API + Azure | smoke, ui, integration, client | pass |
| TC-005 | Admin updates car details and the saved car has the new values | UI + API | regression, ui, admin | **fails: BUG-001** |
| TC-006 | Search by city, category and max price returns exactly the matching cars | API | regression, api, no_login | **fails: BUG-004** |
| TC-007 | Client books a car: total, status, Service Bus event and notifications | API + Azure | smoke, api, integration, client | pass |
| TC-008 | An overlapping booking is refused with 409 | API | regression, api, client | **fails: BUG-002** |
| TC-009 | A client cannot delete another client's car | API | regression, api, security, client | **fails: BUG-003** |
| TC-010 | Admin deletes a car; it disappears from the list and the API returns 404 | UI + API | regression, ui, admin | pass |
| TC-011 | Generated description names make, model and year, is at most 600 characters and has no price | API + LLM | regression, api, llm, costly, client | pass |
| TC-012 | After logout, the browser Back button does not show a private page again | UI | regression, ui, security, client | pass |

---

## TC-001 Admin logs in and sees the dashboard stats

**Preconditions:** the seeded admin accounts exist.

| # | Step | Expected result |
|---|---|---|
| 1 | Open `/login`, log in as an admin | "Welcome back" message |
| 2 | Look at the page | The URL is `/admin`, the admin menu and the stat tiles are visible |
| 3 | Compare the Cars, Users and Active bookings tiles with `GET /admin/stats` | The numbers are the same (read at the same moment) |

## TC-002 Login with a wrong password shows an error and no session

| # | Step | Expected result |
|---|---|---|
| 1 | Open `/login`, enter a real client email and a wrong password, submit | The error "Wrong email or password." is shown |
| 2 | Look at the page | Still on `/login`, the email field keeps the email |
| 3 | Check the cookies, then open `/my/listings` | No `access_token` cookie; the visitor is sent to `/login?next=/my/listings` |

## TC-003 A new client registers through the API and can log in, an inactive user cannot

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /auth/register` with a new email | 201, role `client`, active |
| 2 | Log in with the new account, `GET /auth/me` | 200, the profile has the same email |
| 3 | Register the same email again | 409 |
| 4 | Log in as `inactive@drivenow.test` | 403 `ACCOUNT_INACTIVE` |

**Cleanup:** the new account is deactivated (users cannot be deleted).

## TC-004 Client creates a listing with 3 photos

| # | Step | Expected result |
|---|---|---|
| 1 | Log in as a client, open List your car | The empty form opens |
| 2 | Fill every field (price 47.50, features GPS and Bluetooth), attach 3 JPG photos, Publish | "Car published.", the edit page of the new car opens |
| 3 | Look at the photo panel | 3 photos, the first one marked "Main photo" |
| 4 | `GET /cars/{id}` | Model, price 47.50 and features as entered; photos flagged primary, not, not |
| 5 | Open every photo URL; look up every blob in Azure Blob Storage | 200 `image/jpeg`; every blob exists with the same size |

## TC-005 Admin updates car details

**Preconditions:** a client has a car at 50.00 per day with 30 000 km.

| # | Step | Expected result |
|---|---|---|
| 1 | Log in as an admin, open the edit form of the car | The form shows the current values |
| 2 | Set price 89.99, mileage 31 250, features GPS and Heated seats; Save | "Changes saved." |
| 3 | `GET /cars/{id}` | Price **89.99**, mileage 31 250, features GPS and Heated seats |

**Known bug:** BUG-001 saves the price as 89.00.

## TC-006 Search by city, category and max price

**Preconditions:** four cars in a city nobody else uses: an SUV at 50.00, an SUV at exactly 75.50, an
SUV at 75.51 and an economy car at 40.00.

| # | Step | Expected result |
|---|---|---|
| 1 | As a visitor, `GET /cars?city=<city>&category=suv&max_price=75.50` | Exactly the SUV at 50.00 and the SUV at **75.50**; the boundary is included |

**Known bug:** BUG-004 leaves out the SUV priced exactly at the maximum.

## TC-007 Client books a car

**Preconditions:** client A lists a car at 45.50 per day.

| # | Step | Expected result |
|---|---|---|
| 1 | Client B books it from day 5 to day 8 | 201 |
| 2 | Look at the booking | Status `pending`, 3 days, total 136.50 |
| 3 | Peek the Service Bus subscription `audit` | A `booking.created` event for this booking with total 136.50 and the right owner |
| 4 | `GET /notifications` as A and as B | Both have a notification for this booking (written by the worker) |

## TC-008 An overlapping booking is refused

**Preconditions:** a car booked from day 10 to day 12.

| # | Step | Expected result |
|---|---|---|
| 1 | Book the same car from day 9 to day 14 | **409 `DATES_TAKEN`**, the car is never double booked |

**Known bug:** BUG-002 accepts it (201) because only the start date is checked.

## TC-009 A client cannot delete another client's car

| # | Step | Expected result |
|---|---|---|
| 1 | Client A lists a car | 201 |
| 2 | Client B sends `DELETE /cars/{id}` | **403** |
| 3 | `GET /cars/{id}` | The car still exists |

**Known bug:** BUG-003 lets client B delete it (204).

## TC-010 Admin deletes a car

| # | Step | Expected result |
|---|---|---|
| 1 | A client has a car; an admin opens Admin > Cars and searches its model | The car's row is visible |
| 2 | Delete, confirm in the dialog | "Car deleted." |
| 3 | Search again; `GET /cars/{id}` | No row, "No cars match."; 404 |

## TC-011 Generated description follows the rules

**Preconditions:** a client lists a 2021 Skoda Octavia at 42.50 per day.

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /cars/{id}/generate-description` as the owner | 200 with a description and the provider |
| 2 | Check the text | 1 to 600 characters; mentions Skoda, Octavia and 2021; no price or currency; no markdown |
| 3 | Ask again as another client | 403 |

With `LLM_PROVIDER=anthropic` this test calls the real model (marker `costly`); with `mock` it is free.

## TC-012 After logout, Back does not show a private page

Found during exploratory testing: the browser kept My listings in its cache and showed it again after
logout. Fixed in the platform by sending `Cache-Control: no-store` on every page of a logged-in user.

| # | Step | Expected result |
|---|---|---|
| 1 | Log in as a client, open My listings | The page opens |
| 2 | Log out | "You are logged out." |
| 3 | Press the browser Back button | The login page (`/login?next=/my/listings`) opens; nothing from the private page is shown |
