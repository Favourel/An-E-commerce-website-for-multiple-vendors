function card(stripe_publishable_key, customer_email) {
    document.addEventListener("DOMContentLoaded", function(event){
        var stripe = Stripe(stripe_publishable_key);
        var elements = stripe.elements();

        var style = {
          base: {
            color: '#32325d',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
              color: '#aab7c4'
            }
          },
          invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
          }
        };

        // Create an instance of the card Element.
        var card = elements.create('card', {style: style});
        card.mount("#card-element");

        // Handle real-time validation errors from the card Element.
       card.addEventListener('change', function(event) {
          var displayError = document.getElementById('card-errors');
          if (event.error) {
            displayError.textContent = event.error.message;
          } else {
            displayError.textContent = '';
          }
       });

       // Handle form submission.
       var form = document.getElementById('payment-form');
       form.addEventListener('submit', function(event) {
          event.preventDefault();

          stripe.createToken(card).then(function(result) {
            if (result.error) {
              // Inform the user if there was an error.
              var errorElement = document.getElementById('card-errors');
              errorElement.textContent = result.error.message;
            } else {
              // Create Payment Method BEGIN
              stripe.createPaymentMethod({
                type: 'card',
                card: card,
                billing_details: {
                  email: customer_email,
                },
              }).then(function(payment_method_result){
                if (payment_method_result.error) {
                  var errorElement = document.getElementById('card-errors');
                  errorElement.textContent = payment_method_result.error.message;
                } else {
                  var form = document.getElementById('payment-form');
                  var hiddenInput = document.createElement('input');

                  hiddenInput.setAttribute('type', 'hidden');
                  hiddenInput.setAttribute('name', 'payment_method_id');
                  hiddenInput.setAttribute('value', payment_method_result.paymentMethod.id);

                  form.appendChild(hiddenInput);
                  // Submit the form
                  form.submit();
                };
              });
              // Create Payment Method END
            }
          }); // createToken

       }); // form.addEventListener(..)

    }); // DOMContentLoaded
}

