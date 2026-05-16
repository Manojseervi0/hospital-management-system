function validatePatientForm() {

    let phone = document.forms["patientForm"]["phone"].value;
    let age = document.forms["patientForm"]["age"].value;

    // Phone validation
    if (phone.length !== 10) {

        alert("Phone number must be 10 digits");
        return false;
    }

    // Age validation
    if (age <= 0 || age > 120) {

        alert("Enter valid age");
        return false;
    }

    return true;
}