from prowler.lib.check.models import Check, Check_Report_AWS
from prowler.providers.aws.services.ec2.ec2_client import ec2_client
from prowler.providers.aws.services.ec2.lib.security_groups import check_security_group
from prowler.providers.aws.services.vpc.vpc_client import vpc_client


class ec2_instance_ssh_port_exposed_to_internet(Check):
    def execute(self):
        findings = []
        check_ports = [22]
        for instance in ec2_client.instances:
            report = Check_Report_AWS(self.metadata())
            report.region = instance.region
            report.status = "PASS"
            report.status_extended = f"Instance {instance.id} does not have SSH port 22 open to the Internet."
            report.resource_id = instance.id
            report.resource_arn = instance.arn
            report.resource_tags = instance.tags
            if instance.security_groups:
                for instance_sg in instance.security_groups:
                    for sg in ec2_client.security_groups:
                        if sg.id == instance_sg["GroupId"]:
                            for ingress_rule in sg.ingress_rules:
                                if check_security_group(
                                    ingress_rule, "tcp", check_ports, any_address=True
                                ):
                                    # The port is open, now check if the instance is in a public subnet with a public IP
                                    report.status = "FAIL"
                                    if instance.public_ip:
                                        report.status_extended = f"Instance {instance.id} has SSH exposed to 0.0.0.0/0 on public ip address {instance.public_ip} but in private subnet {instance.subnet_id}."
                                        report.check_metadata.Severity = "high"
                                        if vpc_client.vpc_subnets[
                                            instance.subnet_id
                                        ].public:
                                            report.status_extended = f"Instance {instance.id} has SSH exposed to 0.0.0.0/0 on public ip address {instance.public_ip} in public subnet {instance.subnet_id}."
                                            report.check_metadata.Severity = "critical"
                                    else:
                                        report.status_extended = f"Instance {instance.id} has SSH exposed to 0.0.0.0/0 but with no public ip address."
                                        report.check_metadata.Severity = "medium"
                                    break
            findings.append(report)
        return findings
