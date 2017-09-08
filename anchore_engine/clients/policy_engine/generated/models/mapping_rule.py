# coding: utf-8

"""
    anchore_engine.services.policy_engine

    This is a policy evaluation service. It receives push-events from external systems for data updates and provides an api for requesting image policy checks

    OpenAPI spec version: 1.0.0
    Contact: zach@anchore.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


from pprint import pformat
from six import iteritems
import re


class MappingRule(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """
    def __init__(self, id=None, name=None, whitelist_ids=None, policy_id=None, registry=None, repository=None, image=None):
        """
        MappingRule - a model defined in Swagger

        :param dict swaggerTypes: The key is attribute name
                                  and the value is attribute type.
        :param dict attributeMap: The key is attribute name
                                  and the value is json key in definition.
        """
        self.swagger_types = {
            'id': 'str',
            'name': 'str',
            'whitelist_ids': 'list[str]',
            'policy_id': 'str',
            'registry': 'str',
            'repository': 'str',
            'image': 'ImageRef'
        }

        self.attribute_map = {
            'id': 'id',
            'name': 'name',
            'whitelist_ids': 'whitelist_ids',
            'policy_id': 'policy_id',
            'registry': 'registry',
            'repository': 'repository',
            'image': 'image'
        }

        self._id = id
        self._name = name
        self._whitelist_ids = whitelist_ids
        self._policy_id = policy_id
        self._registry = registry
        self._repository = repository
        self._image = image

    @property
    def id(self):
        """
        Gets the id of this MappingRule.

        :return: The id of this MappingRule.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """
        Sets the id of this MappingRule.

        :param id: The id of this MappingRule.
        :type: str
        """

        self._id = id

    @property
    def name(self):
        """
        Gets the name of this MappingRule.

        :return: The name of this MappingRule.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        Sets the name of this MappingRule.

        :param name: The name of this MappingRule.
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")

        self._name = name

    @property
    def whitelist_ids(self):
        """
        Gets the whitelist_ids of this MappingRule.

        :return: The whitelist_ids of this MappingRule.
        :rtype: list[str]
        """
        return self._whitelist_ids

    @whitelist_ids.setter
    def whitelist_ids(self, whitelist_ids):
        """
        Sets the whitelist_ids of this MappingRule.

        :param whitelist_ids: The whitelist_ids of this MappingRule.
        :type: list[str]
        """
        if whitelist_ids is None:
            raise ValueError("Invalid value for `whitelist_ids`, must not be `None`")

        self._whitelist_ids = whitelist_ids

    @property
    def policy_id(self):
        """
        Gets the policy_id of this MappingRule.

        :return: The policy_id of this MappingRule.
        :rtype: str
        """
        return self._policy_id

    @policy_id.setter
    def policy_id(self, policy_id):
        """
        Sets the policy_id of this MappingRule.

        :param policy_id: The policy_id of this MappingRule.
        :type: str
        """
        if policy_id is None:
            raise ValueError("Invalid value for `policy_id`, must not be `None`")

        self._policy_id = policy_id

    @property
    def registry(self):
        """
        Gets the registry of this MappingRule.

        :return: The registry of this MappingRule.
        :rtype: str
        """
        return self._registry

    @registry.setter
    def registry(self, registry):
        """
        Sets the registry of this MappingRule.

        :param registry: The registry of this MappingRule.
        :type: str
        """
        if registry is None:
            raise ValueError("Invalid value for `registry`, must not be `None`")

        self._registry = registry

    @property
    def repository(self):
        """
        Gets the repository of this MappingRule.

        :return: The repository of this MappingRule.
        :rtype: str
        """
        return self._repository

    @repository.setter
    def repository(self, repository):
        """
        Sets the repository of this MappingRule.

        :param repository: The repository of this MappingRule.
        :type: str
        """
        if repository is None:
            raise ValueError("Invalid value for `repository`, must not be `None`")

        self._repository = repository

    @property
    def image(self):
        """
        Gets the image of this MappingRule.

        :return: The image of this MappingRule.
        :rtype: ImageRef
        """
        return self._image

    @image.setter
    def image(self, image):
        """
        Sets the image of this MappingRule.

        :param image: The image of this MappingRule.
        :type: ImageRef
        """
        if image is None:
            raise ValueError("Invalid value for `image`, must not be `None`")

        self._image = image

    def to_dict(self):
        """
        Returns the model properties as a dict
        """
        result = {}

        for attr, _ in iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self.to_dict())

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()

    def __eq__(self, other):
        """
        Returns true if both objects are equal
        """
        if not isinstance(other, MappingRule):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """
        Returns true if both objects are not equal
        """
        return not self == other