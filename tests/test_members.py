import unittest

from XRoad.Members import Members


class TestMembers(unittest.TestCase):

    def test_initialization_with_full_path(self):
        member = Members(objectType="SERVICE", memberPath="instance/class/code/subsystem/service/serviceVersion")

        self.assertEqual(member.xRoadInstance, "instance")
        self.assertEqual(member.memberClass, "class")
        self.assertEqual(member.memberCode, "code")
        self.assertEqual(member.subsystemCode, "subsystem")
        self.assertEqual(member.serviceCode, "service")
        self.assertEqual(member.serviceVersion, "serviceVersion")

    def test_initialization_with_partial_path(self):
        member = Members(objectType="SERVICE", memberPath="instance/class")

        self.assertEqual(member.xRoadInstance, "instance")
        self.assertEqual(member.memberClass, "class")
        self.assertIsNone(member.memberCode)
        self.assertIsNone(member.subsystemCode)
        self.assertIsNone(member.serviceCode)
        self.assertIsNone(member.serviceVersion)

    def test_wsdl_path_generation(self):
        member = Members(objectType="SERVICE", memberPath="instance/class/code/subsystem/service/serviceVersion")
        expected_wsdl_path = "xRoadInstance=instance/memberClass=class/memberCode=code/subsystemCode=subsystem/serviceCode=service/version=serviceVersion"

        self.assertEqual(member.wsdl_path, expected_wsdl_path)

    def test_wsdl_url(self):
        member = Members(objectType="SERVICE", memberPath="instance/class/code/subsystem/service/serviceVersion")
        ssu = "http://example.com"
        expected_wsdl_path = "xRoadInstance=instance/memberClass=class/memberCode=code/subsystemCode=subsystem/serviceCode=service/version=serviceVersion"
        expected_url = f"{ssu}/wsdl?{expected_wsdl_path}"

        self.assertEqual(member.wsdl_url(ssu), expected_url)

    def test_member_dict(self):
        member = Members(objectType="SERVICE", memberPath="instance/class/code/subsystem/service/serviceVersion")
        expected_dict = {
            'xRoadInstance': "instance",
            'memberClass': "class",
            'memberCode': "code",
            'subsystemCode': "subsystem",
            'serviceCode': "service",
            'serviceVersion': "serviceVersion",
            'objectType': "SERVICE"
        }

        self.assertDictEqual(member.member_dict, expected_dict)

    def test_wsdl_path_none_for_non_service(self):
        member = Members(objectType="OTHER_TYPE", memberPath="instance/class/code/subsystem/service/serviceVersion")
        try:
            path = member.wsdl_path
        except Exception as e:
            self.assertEqual(str(e), "wsdl_path is only available for SERVICE objectType")


if __name__ == '__main__':
    unittest.main()
