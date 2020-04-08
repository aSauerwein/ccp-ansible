#!/usr/bin/python

# Copyright: (c) 2020, NTS Netzwerk Telekom Service AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}
DOCUMENTATION = """
---
module: ccp

short_description: Module to interact with Cisco Container Platform REST API

version_added: '2.9'

description:
    - ' Directo REST API for Configuration of Cisco Container Platform'

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

author:
    - Andreas Sauerwein (@ASauerwein)
"""


# from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.urls import open_url, fetch_url


def get_object_by_field(object_list, value, field="name", contains=False):
    """
    Iterate through an list of object and returns
    the first element that matches the criteria
    if supplied object is a dict convert it to a list
    """
    if isinstance(object_list, dict):
        object_list = [object_list]
    if contains:
        for element in object_list:
            if isinstance(element, str):
                if value in element:
                    return element
            else:
                if value in element:
                    return element
    else:
        for element in object_list:
            if isinstance(element, str):
                if value == element:
                    return element
            else:
                if value == element[field]:
                    return element

    return None


def compare_dict(current: dict, new: dict):
    """
    Compares 2 Dictionaries based on there keys
    if a key exists in current but not in new it is ignored
    return:
        true: no difference between the dictionaries
        false: difference found
    """
    if current == new:
        # dictionarys are identical
        return True
    else:
        # itearate over all fields in the new dictionary
        # and compare it with the current dictionary
        for key, new_value in new.items():
            if key in current:
                if new_value == current[key]:
                    # matching
                    pass
                elif isinstance(new_value, dict):
                    if compare_dict(current[key], new_value):
                        pass
                    else:
                        return False
                elif isinstance(new_value, list):
                    # if is a list of dictionaries resume operation
                    for list_index, list_element in enumerate(new_value):
                        if isinstance(list_element, dict):
                            if "name" in list_element:
                                current_list_element = get_object_by_field(
                                    current[key], list_element["name"]
                                )
                            else:
                                current_list_element = current[key][list_index]
                            if compare_dict(current_list_element, list_element):
                                pass
                            else:
                                return False

                else:
                    return False

            else:
                # key missing in current config
                # check if value contains anything
                # i.e empty lists should be ignored
                if new_value:
                    return False
                else:
                    pass

        return True


def login(module):
    """
    Login to CCP, either with V2 or V2
    """
    options = {}
    version = module.params.get("version")
    username = module.params.get("username")
    password = module.params.get("password")

    target_url = ""
    if version == 2:
        # api v2 login code
        options["headers"] = {"content-type": "application/json"}
        options["method"] = "POST"
        query_params = "?username={}&password={}".format(username, password)
        target_url = module.params.get("base_url") + "/2/system/login" + query_params
    elif version == 3:
        # api v3 login code
        options["headers"] = {"content-type": "application/x-www-form-urlencoded"}
        options["data"] = "username={}&password={}".format(username, password)
        target_url = module.params.get("base_url") + "/v3/system/login"
    else:
        module.fail_json(msg="Unsupported Version {}".format(version))

    response, info = fetch_url(module, url=target_url, **options,)

    if response.code == 200:
        if version == 2:
            module.params["cookies"] = info["cookies"]
            module.params["token"] = info["x-auth-token"]
        else:
            module.params["token"] = info["x-auth-token"]
        return response
    else:
        module.fail_json(msg="Login Failed {}".format(response.msg))


def call_api(module, method="GET"):
    options = {}
    target_url = module.params.get("base_url")
    version = module.params.get("version")
    if version == 3:
        # version 3 will be used
        target_url += "/v3"
    elif version == 2:
        # version 3 will be used
        target_url += "/2"
    else:
        module.fail_json(msg="Unsupported Version {}".format(version))

    # adding resource path to target_url
    target_url += module.params.get("resource_path")

    # handling query params

    if module.params.get("query_params"):
        query_param_string = ""
        first_param = True
        for key, value in module.params.get("query_params").items():
            query_param_string += "?" if first_param else "&"
            first_param = False
            query_param_string += f"{key}={value}"

        # adding query_param_string to target_url
        target_url += query_param_string

    # get api_body from module params if method is post or put
    if method in ("POST", "PATCH"):
        api_body = json.dumps(module.params.get("api_body"))
    else:
        api_body = None

    options["headers"] = {"content-type": "application/json"}
    options["headers"]["x-auth-token"] = module.params.get("token", "")
    options["cookies"] = module.params.get("cookies")
    module.params["follow_redirects"] = False

    response, info = fetch_url(
        module, method=method, url=target_url, data=api_body, **options
    )

    if info["status"] == 200:  # success
        return json.loads(response.read())
    if info["status"] == 202:  # accepted
        return json.loads(response.read())
    elif info["status"] == 204:  # deleted
        return "Successfully deleted"
    elif (
        info["status"] == 404
        and module.params.get("state") == "absent"
        and method == "GET"
    ):
        # object already deleted
        return None
    else:
        module.fail_json(msg="Api Error: {}".format(info))


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(type="int", default=3),
            resource_path=dict(type="str", default=None, required=True),
            base_url=dict(type="str", default=None, required=True),
            username=dict(type="str", default=None, required=True),
            password=dict(type="str", default=None, required=True),
            api_body=dict(type="dict", default=None),
            query_params=dict(type="dict", default=None),
            validate_certs=dict(type="bool", default=True, required=False),
            filter=dict(type="dict", default=None, required=False),
            state=dict(type="str", choices=["absent", "present"], default="present"),
        )
    )

    # create result object
    result = {"changed": False, "api_body": ""}
    result["params"] = json.dumps(module.params)

    # login to ccp api
    login_result = login(module)
    # get request on resouce
    get_response = call_api(module)
    
    # if filter supplied filter the response
    filter_by = module.params.get("filter")
    if filter_by:
        if module.params.get("api_body"):
            module.fail_json(msg="Filter and API_Body are mutual exclusive")
        filtered_response = get_response
        for key, value in filter_by.items():
            filtered_response = get_object_by_field(filtered_response, value, field=key)
            if not filtered_response:
                # exit loop before trying the other elements
                break
        if filtered_response is None:
            module.fail_json(msg="No Object with the given filter {} found in {}".format(filter_by, get_response))
        get_response = filtered_response




    api_body = module.params.get("api_body")
    request_change = False
    request_create = False
    request_delete = False
    current_config = ""

    if module.params.get("state") == "present":
        # try to get the current config by name
        if api_body:
            if api_body.get("name"):
                current_config = get_object_by_field(get_response, api_body.get("name"))
            else:
                request_create = True

            if current_config:
                # check differences
                difference = not compare_dict(current_config, api_body)
                if difference:
                    request_change = True
                    module.params["resource_path"] += current_config["id"] + "/"
                else:
                    request_change = False
            else:
                request_create = True
        else:
            # nothing to do
            pass
    elif module.params.get("state") == "absent":
        # check if object still exists
        # if the get_response is empty, the api returned a 404
        if get_response:
            if api_body.get("name"):
                current_config = get_object_by_field(get_response, api_body.get("name"))
                # prepare delete request
                module.params["resource_path"] += current_config["id"] + "/"
                request_delete = True
            else:
                # assume that there is already a uuid in the request
                request_delete = True
        else:
            result["changed"] = False

    # POST
    if request_create:
        method = "POST"
    elif request_change:
        method = "PATCH"
    elif request_delete:
        method = "DELETE"
    else:
        method = "GET"

    if method in ("POST", "PATCH", "DELETE"):
        response = call_api(module, method=method)
        result["api_body"] = module.params.get("api_body")
        result["changed"] = True
    else:
        # return only 1 element if there's a name in the api_body
        response = current_config or get_response

    result["api_response"] = response
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
