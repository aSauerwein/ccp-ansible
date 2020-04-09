ccp Ansible Collection
=========

Ansible collection for managing and automtaic Cisco Container Platform ( CCP ).

Requirements
------------

- No special requirements

Plugin Variables
--------------
```
options:
    version:
        description:
            - WHich API Version to use. Valid Values 2, 3
        required: true
        type: str
    resource_path:
        description:
            - Resource URI being configured related to api_uri.
        required: true
        type: str
    base_url:
        description:
            - Base URL of the API i.e. the https://[CCP-IP]
        required: true
        type: str
    username:
        description:
            - Username for CCP
        required: false
        type: str
    password:
        description:
            - Password for CCP
        required: false
        type: str
    api_body:
        description:
            - The payload for API requests used to modify resources.
        required: false
        type: dict
    query_params:
        description:
            - query params appended to the URL
        required: false
        type: dict
    validate_certs:
        description:
            - define if certs should be validated
        required: false
        default: true
        type: bool
    filter:
        description:
            - filters the returned values on given field
            - i.e. if filter { name: test } the first object with the name test will be returned
        required: false
        default: {}
        type: dict
    state:
        description:
        - If C(present), will verify the resource is present and will create if needed.
        - If C(absent), will verify the resource is absent and will delete if needed.
        choices: [present, absent]
        default: present
```
Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

There is an example Playbook in the Playbooks folder.


License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
