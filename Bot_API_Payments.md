Bot API: Payments
https://core.telegram.org/bots/api#payments

Your bot can accept payments from Telegram users. Please see the introduction to payments for more details on the process and how to set up payments for your bot.

sendInvoice
Use this method to send invoices. On success, the sent Message is returned.

Parameter	Type	Required	Description
chat_id	Integer or String	Yes	Unique identifier for the target chat or username of the target channel (in the format @channelusername)
message_thread_id	Integer	Optional	Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
direct_messages_topic_id	Integer	Optional	Identifier of the direct messages topic to which the message will be sent; required if the message is sent to a direct messages chat
title	String	Yes	Product name, 1-32 characters
description	String	Yes	Product description, 1-255 characters
payload	String	Yes	Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use it for your internal processes.
provider_token	String	Optional	Payment provider token, obtained via @BotFather. Pass an empty string for payments in Telegram Stars.
currency	String	Yes	Three-letter ISO 4217 currency code, see more on currencies. Pass “XTR” for payments in Telegram Stars.
prices	Array of LabeledPrice	Yes	Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.). Must contain exactly one item for payments in Telegram Stars.
max_tip_amount	Integer	Optional	The maximum accepted amount for tips in the smallest units of the currency (integer, not float/double). For example, for a maximum tip of US$ 1.45 pass max_tip_amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0. Not supported for payments in Telegram Stars.
suggested_tip_amounts	Array of Integer	Optional	A JSON-serialized array of suggested amounts of tips in the smallest units of the currency (integer, not float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
start_parameter	String	Optional	Unique deep-linking parameter. If left empty, forwarded copies of the sent message will have a Pay button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a URL button with a deep link to the bot (instead of a Pay button), with the value used as the start parameter
provider_data	String	Optional	JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
photo_url	String	Optional	URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
photo_size	Integer	Optional	Photo size in bytes
photo_width	Integer	Optional	Photo width
photo_height	Integer	Optional	Photo height
need_name	Boolean	Optional	Pass True if you require the user's full name to complete the order. Ignored for payments in Telegram Stars.
need_phone_number	Boolean	Optional	Pass True if you require the user's phone number to complete the order. Ignored for payments in Telegram Stars.
need_email	Boolean	Optional	Pass True if you require the user's email address to complete the order. Ignored for payments in Telegram Stars.
need_shipping_address	Boolean	Optional	Pass True if you require the user's shipping address to complete the order. Ignored for payments in Telegram Stars.
send_phone_number_to_provider	Boolean	Optional	Pass True if the user's phone number should be sent to the provider. Ignored for payments in Telegram Stars.
send_email_to_provider	Boolean	Optional	Pass True if the user's email address should be sent to the provider. Ignored for payments in Telegram Stars.
is_flexible	Boolean	Optional	Pass True if the final price depends on the shipping method. Ignored for payments in Telegram Stars.
disable_notification	Boolean	Optional	Sends the message silently. Users will receive a notification with no sound.
protect_content	Boolean	Optional	Protects the contents of the sent message from forwarding and saving
allow_paid_broadcast	Boolean	Optional	Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
message_effect_id	String	Optional	Unique identifier of the message effect to be added to the message; for private chats only
suggested_post_parameters	SuggestedPostParameters	Optional	A JSON-serialized object containing the parameters of the suggested post to send; for direct messages chats only. If the message is sent as a reply to another suggested post, then that suggested post is automatically declined.
reply_parameters	ReplyParameters	Optional	Description of the message to reply to
reply_markup	InlineKeyboardMarkup	Optional	A JSON-serialized object for an inline keyboard. If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.

createInvoiceLink
Use this method to create a link for an invoice. Returns the created invoice link as String on success.

Parameter	Type	Required	Description
business_connection_id	String	Optional	Unique identifier of the business connection on behalf of which the link will be created. For payments in Telegram Stars only.
title	String	Yes	Product name, 1-32 characters
description	String	Yes	Product description, 1-255 characters
payload	String	Yes	Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use it for your internal processes.
provider_token	String	Optional	Payment provider token, obtained via @BotFather. Pass an empty string for payments in Telegram Stars.
currency	String	Yes	Three-letter ISO 4217 currency code, see more on currencies. Pass “XTR” for payments in Telegram Stars.
prices	Array of LabeledPrice	Yes	Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.). Must contain exactly one item for payments in Telegram Stars.
subscription_period	Integer	Optional	The number of seconds the subscription will be active for before the next payment. The currency must be set to “XTR” (Telegram Stars) if the parameter is used. Currently, it must always be 2592000 (30 days) if specified. Any number of subscriptions can be active for a given bot at the same time, including multiple concurrent subscriptions from the same user. Subscription price must no exceed 10000 Telegram Stars.
max_tip_amount	Integer	Optional	The maximum accepted amount for tips in the smallest units of the currency (integer, not float/double). For example, for a maximum tip of US$ 1.45 pass max_tip_amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0. Not supported for payments in Telegram Stars.
suggested_tip_amounts	Array of Integer	Optional	A JSON-serialized array of suggested amounts of tips in the smallest units of the currency (integer, not float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
provider_data	String	Optional	JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
photo_url	String	Optional	URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service.
photo_size	Integer	Optional	Photo size in bytes
photo_width	Integer	Optional	Photo width
photo_height	Integer	Optional	Photo height
need_name	Boolean	Optional	Pass True if you require the user's full name to complete the order. Ignored for payments in Telegram Stars.
need_phone_number	Boolean	Optional	Pass True if you require the user's phone number to complete the order. Ignored for payments in Telegram Stars.
need_email	Boolean	Optional	Pass True if you require the user's email address to complete the order. Ignored for payments in Telegram Stars.
need_shipping_address	Boolean	Optional	Pass True if you require the user's shipping address to complete the order. Ignored for payments in Telegram Stars.
send_phone_number_to_provider	Boolean	Optional	Pass True if the user's phone number should be sent to the provider. Ignored for payments in Telegram Stars.
send_email_to_provider	Boolean	Optional	Pass True if the user's email address should be sent to the provider. Ignored for payments in Telegram Stars.
is_flexible	Boolean	Optional	Pass True if the final price depends on the shipping method. Ignored for payments in Telegram Stars.

answerShippingQuery
If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.

Parameter	Type	Required	Description
shipping_query_id	String	Yes	Unique identifier for the query to be answered
ok	Boolean	Yes	Pass True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)
shipping_options	Array of ShippingOption	Optional	Required if ok is True. A JSON-serialized array of available shipping options.
error_message	String	Optional	Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. “Sorry, delivery to your desired address is unavailable”). Telegram will display this message to the user.
answerPreCheckoutQuery
Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. Use this method to respond to such pre-checkout queries. On success, True is returned. Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

Parameter	Type	Required	Description
pre_checkout_query_id	String	Yes	Unique identifier for the query to be answered
ok	Boolean	Yes	Specify True if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use False if there are any problems.
error_message	String	Optional	Required if ok is False. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.
getMyStarBalance
A method to get the current Telegram Stars balance of the bot. Requires no parameters. On success, returns a StarAmount object.

getStarTransactions
Returns the bot's Telegram Star transactions in chronological order. On success, returns a StarTransactions object.

Parameter	Type	Required	Description
offset	Integer	Optional	Number of transactions to skip in the response
limit	Integer	Optional	The maximum number of transactions to be retrieved. Values between 1-100 are accepted. Defaults to 100.