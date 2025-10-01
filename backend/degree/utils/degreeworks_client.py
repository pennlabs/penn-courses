import json
from pathlib import Path

from requests import Session

from degree.models import Degree


BASE_URL = "https://degreeworks-prod-j.isc-seo.upenn.edu:9904"  # "128.91.225.72:9904"


class DegreeworksClient:
    def __init__(self, auth_token, refresh_token, pennid, name):
        self.auth_token = auth_token
        self.refresh_token = refresh_token
        self.pennid = pennid
        self.name = name
        self.s = Session()
        cookies = {
            "REFRESH_TOKEN": refresh_token,
            "NAME": name,
            "X-AUTH-TOKEN": auth_token,
        }
        headers = {
            "Host": "degreeworks-prod-j.isc-seo.upenn.edu:9904",
            "Origin": f"{BASE_URL}",
        }
        self.s.cookies.update(cookies)
        self.s.headers.update(headers)

    def audit(self, degree: Degree, timeout=30) -> dict:
        payload = {
            "studentId": self.pennid,
            "isIncludeInprogress": True,
            "isIncludePreregistered": True,
            "isKeepCurriculum": False,
            "school": "UG",
            "degree": degree.degree,
            "catalogYear": str(degree.year),
            "goals": [
                {"code": "MAJOR", "value": degree.major},
                {"code": "CONC", "value": degree.concentration},
                {"code": "PROGRAM", "value": degree.program},
                {"code": "COLLEGE", "value": degree.program.split("_")[0]},
            ],
            "classes": [],
        }

        res = self.s.post(
            f"{BASE_URL}/api/audit",
            json=payload,
            timeout=timeout,
        )

        res.raise_for_status()

        return res.json()

    def degrees_of(self, program_code: str, year: int, undergrad_only=False) -> list[Degree]:
        goals_payload = [
            {
                "id": "programCollection",
                "description": "Program",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "catalogYear",
                        "description": "Catalog year",
                        "entityName": "catalogYears",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/catalogYears",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": ["2024"],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "program",
                        "description": "Program",
                        "entityName": "programs",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "NP_PHD_JOINT",
                                "description": "*Nursing Joint PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_BIOD_U",
                                "description": "*Seven Yr Bio-Dent Pgrm Pre-Maj",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CP_MA",
                                "description": "Annenberg - MA (PhD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CP_PHD",
                                "description": "Annenberg - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA",
                                "description": "Arts & Sciences - BA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_UNDC",
                                "description": "Arts & Sciences - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_PHD_JOINT",
                                "description": "Arts & Sciences - Joint PhD Degree",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MA",
                                "description": "Arts & Sciences - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MPHIL",
                                "description": "Arts & Sciences - MPhil",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MS",
                                "description": "Arts & Sciences - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_PHD",
                                "description": "Arts & Sciences - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_CERTF_DM",
                                "description": "Dental - Certificate (Post-Graduate FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_CERT_DM",
                                "description": "Dental - Certificate (Post-Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD",
                                "description": "Dental - Doctor of Dental Medicine",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD_BIOD",
                                "description": "Dental - Doctor of Dental Medicine (7-yr)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD_PASS",
                                "description": "Dental - Doctor of Dental Medicine (Advanced)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_DSCD",
                                "description": "Dental - Doctor of Science in Dentistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MADS",
                                "description": "Dental - Master of Advance Dental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MOHS",
                                "description": "Dental - Master of Oral Health Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MSOB",
                                "description": "Dental - Master of Science in Oral Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_CERT_GR",
                                "description": "Design - Certificate (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_CERT_PR",
                                "description": "Design - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_MA",
                                "description": "Design - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_MS",
                                "description": "Design - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MARCH",
                                "description": "Design - Master of Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MCP",
                                "description": "Design - Master of City Planning",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MEBD",
                                "description": "Design - Master of Environmental Building Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MFA",
                                "description": "Design - Master of Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MLA",
                                "description": "Design - Master of Landscape Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MSDES",
                                "description": "Design - Master of Science in Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MSHP",
                                "description": "Design - Master of Science in Historic Preserv",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MUSA",
                                "description": "Design - Master of Urban Spatial Analytics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_PHD",
                                "description": "Design - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_CMPC_U",
                                "description": "Dual Degree - Computer & Cog Sci - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_HUNTS",
                                "description": "Dual Degree - Huntsman - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_HUNTS",
                                "description": "Dual Degree - Huntsman - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MA_LAUD",
                                "description": "Dual Degree - Lauder - MA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_LAUD",
                                "description": "Dual Degree - Lauder - MBA - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_MANT",
                                "description": "Dual Degree - M & T - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MANT",
                                "description": "Dual Degree - M & T - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MAT_U",
                                "description": "Dual Degree - M & T - BS - Wharton (Pre-Conc)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MANT",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MAT_U",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BSN - Nursing",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPR_U",
                                "description": "Dual Degree - VIPER - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPER",
                                "description": "Dual Degree - VIPER - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_VIPER",
                                "description": "Dual Degree - VIPER - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIPER",
                                "description": "Dual Degree - VIPER - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIP_U",
                                "description": "Dual Degree - VIPER - BSE - SEAS - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton-Pre-Conc",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_CE",
                                "description": "GSE - Certificate (Continuing Ed.)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_ONL",
                                "description": "GSE - Certificate (Online Continuing Ed.)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_PR",
                                "description": "GSE - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_CERT_GR",
                                "description": "GSE - Certificate (Research)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERTF_PR",
                                "description": "GSE - Certificate - UTRP/Sch Leadership (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_EDD",
                                "description": "GSE - Doctor of Education (EdD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MSED",
                                "description": "GSE - MS in Education (MSEd)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MSED_ONL",
                                "description": "GSE - MS in Education - Online (MSED)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MPHILE",
                                "description": "GSE - Master of Philosophy in Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_PHD",
                                "description": "GSE - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_PHD_JOINT",
                                "description": "GSE Joint Phd",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_MSED",
                                "description": "GSE Master of Sci in Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_MS",
                                "description": "GSE Master of Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LR_JD_JDMBA",
                                "description": "LAW JD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_BAAS_ONL",
                                "description": "LPS - Bachelor of Applied Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_BFA",
                                "description": "LPS - Bachelor of Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_CERTF_PR",
                                "description": "LPS - Certificate (Professional FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_CERT_PR",
                                "description": "LPS - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CERTA_OL",
                                "description": "LPS - Certificate (Undergraduate Advanced Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_CERTF_UG",
                                "description": "LPS - Certificate (Undergraduate FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CRT_UG_OL",
                                "description": "LPS - Certificate (Undergraduate Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MPHIL",
                                "description": "LPS - MPhil",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSAG",
                                "description": "LPS - MS in Applied Geosciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSOD",
                                "description": "LPS - MS in Organizational Dynamics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MAPP",
                                "description": "LPS - Master of Applied Positive Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MBDS",
                                "description": "LPS - Master of Behavioral & Decision Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MCS",
                                "description": "LPS - Master of Chemical Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MES",
                                "description": "LPS - Master of Environmental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MLIBA",
                                "description": "LPS - Master of Liberal Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MPA",
                                "description": "LPS - Master of Public Administration",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSAG_ONL",
                                "description": "LPS MS in Appl Geosci Online",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_CERT",
                                "description": "Law - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LD_SJD",
                                "description": "Law - Doctorate of the Science of Law (SJD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LR_JD",
                                "description": "Law - Juris Doctor (JD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_MLAW",
                                "description": "Law - Master in Law (ML)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_LLM",
                                "description": "Law - Master of Laws (LLM)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_LLCM",
                                "description": "Law - Masters in Comparative Law (LLCM)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_CERT_GR",
                                "description": "Medicine - Certificate (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERT_ONL",
                                "description": "Medicine - Certificate (Online Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERTF_PR",
                                "description": "Medicine - Certificate (Professional FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERT_PR",
                                "description": "Medicine - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MR_MD",
                                "description": "Medicine - MD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_MS",
                                "description": "Medicine - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MBE",
                                "description": "Medicine - Master of Bioethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MBMI",
                                "description": "Medicine - Master of Biomedical Informatics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MHCI_ONL",
                                "description": "Medicine - Master of Health Care Innovation",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MHQS",
                                "description": "Medicine - Master of Healthcare Quality and Safety",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MPH",
                                "description": "Medicine - Master of Public Health",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MRA",
                                "description": "Medicine - Master of Regulatory Affairs",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MRA_ONL",
                                "description": "Medicine - Master of Regulatory Affairs (ONL)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSCE",
                                "description": "Medicine - Master of Science in Clin Epidemiology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSGC",
                                "description": "Medicine - Master of Science in Genetic Counseling",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MPR",
                                "description": "Medicine - Master of Science in Health Pol Resrch",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSME",
                                "description": "Medicine - Master of Science in Medical Ethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSMP",
                                "description": "Medicine - Master of Science in Medical Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSRS",
                                "description": "Medicine - Master of Science in Regulatory Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSTR",
                                "description": "Medicine - Master of Science in Translatnal Resrch",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD",
                                "description": "Medicine - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN",
                                "description": "Nursing - BSN",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NAP",
                                "description": "Nursing - BSN (Accelerated)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_PMN",
                                "description": "Nursing - Certificate (Post-Masters)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_CERT_PR",
                                "description": "Nursing - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ND_DNP",
                                "description": "Nursing - Doctor of Nursing Practice",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ND_DNP_ONL",
                                "description": "Nursing - Doctor of Nursing Practice (Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NP_MS",
                                "description": "Nursing - MS (PhD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_MSN",
                                "description": "Nursing - MSN",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NP_PHD",
                                "description": "Nursing - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD_MDPHD",
                                "description": "PSOM Doctor of Philosophy/MD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD_VRPHD",
                                "description": "PSOM Doctor of Philosophy/VMD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE",
                                "description": "SEAS - BSE",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_CD",
                                "description": "SEAS - BSE - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS",
                                "description": "SEAS - Bachelor of Applied Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_CD",
                                "description": "SEAS - Bachelor of Applied Science - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EX_MSE",
                                "description": "SEAS - Executive MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MCIT",
                                "description": "SEAS - MCIT (On Campus)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MCIT_ONL",
                                "description": "SEAS - MCIT (Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MSE",
                                "description": "SEAS - MSE",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MBIOT",
                                "description": "SEAS - Master of Biotechnology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MIPD",
                                "description": "SEAS - Master of Intg Prod Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EP_PHD",
                                "description": "SEAS - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_CERT_PR",
                                "description": "SEAS Professional Certificate",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_CERT_ONL",
                                "description": "SEAS Professional Certificate (Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SP_PHD_JOINT",
                                "description": "SP2 Joint Phd",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSNPL",
                                "description": "Social Policy & Prac - MS in Non-Profit Leadership",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSNPL_ONL",
                                "description": "Social Policy & Prac - MS in Non-Profit Leadership",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SD_DSW_ONL",
                                "description": "Social Policy & Practice - Doctor of Social Work",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSSP",
                                "description": "Social Policy & Practice - MS in Social Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSW",
                                "description": "Social Policy & Practice - Master of Social Work",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SP_PHD",
                                "description": "Social Policy & Practice - PhD in Social Welfare",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VM_MSAWB_ONL",
                                "description": "VET Mstr of Sci Ani Wlfr Bhvr",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VM_CERT_ONL",
                                "description": "Vet - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VR_VMD",
                                "description": "Vet - PhD/Doctor of Veterinary Medicine",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VP_VMD",
                                "description": "Vet - Veterinariae Medicinae Doctoris-VMD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_JDMBA",
                                "description": "WH JD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EBMBA",
                                "description": "WH MBA/MBIOT",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_ECMBA",
                                "description": "WH MBA/MCIT",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_FMMBA",
                                "description": "WH MBA/MFA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EIMBA",
                                "description": "WH MBA/MIPD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EMMBA",
                                "description": "WH MBA/MSEng",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_MDMBA",
                                "description": "WH MD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_VRMBA",
                                "description": "WH VMD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS",
                                "description": "Wharton - BS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_WUNG",
                                "description": "Wharton - BS - Pre Concentration",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WX_MBA_PHL",
                                "description": "Wharton - Executive MBA (Philadelphia)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WX_MBA_SFO",
                                "description": "Wharton - Executive MBA (San Francisco)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_PHD_JOINT",
                                "description": "Wharton - Joint PhD Degree",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_MA",
                                "description": "Wharton - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA",
                                "description": "Wharton - MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_MS",
                                "description": "Wharton - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_PHD",
                                "description": "Wharton - PhD",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": ["WU_BS_WUNG"],
                        "ruleGoalCode": "PROGRAM",
                        "links": [],
                    },
                    {
                        "name": "school",
                        "description": "Level",
                        "entityName": "schools",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "UG",
                                "description": "Undergraduate",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["UG"],
                        "ruleGoalCode": "SCHOOL",
                        "links": [],
                    },
                    {
                        "name": "college",
                        "description": "College",
                        "entityName": "colleges",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "WU",
                                "description": "Wharton Undergraduate",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["WU"],
                        "ruleGoalCode": "COLLEGE",
                        "links": [],
                    },
                    {
                        "name": "degree",
                        "description": "Degree",
                        "entityName": "degrees",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "BS",
                                "description": "Bachelor of Sci in Economics",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["BS"],
                        "ruleGoalCode": "DEGREE",
                        "links": [],
                    },
                ],
            },
            {
                "id": "curriculumCollection",
                "description": "Areas of study",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "major",
                        "description": "Major",
                        "entityName": "majors",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "WUNG",
                                "description": "Wharton Ung Prgm - Undeclared",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["WUNG"],
                        "ruleGoalCode": "MAJOR",
                        "links": [],
                    },
                    {
                        "name": "concentration",
                        "description": "Concentration",
                        "entityName": "concentrations",
                        "isDisabled": True,
                        "isDriver": False,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": "CONC",
                        "links": [],
                    },
                    {
                        "name": "minor",
                        "description": "Minor",
                        "entityName": "minors",
                        "isDisabled": False,
                        "isDriver": False,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "ACRL",
                                "description": "Actuarial Mathematics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AFRC",
                                "description": "Africana Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AMPP",
                                "description": "American Public Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ASL",
                                "description": "American Sign Lang/Deaf Stds",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANCH",
                                "description": "Ancient History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANEN",
                                "description": "Ancient Near East",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANTH",
                                "description": "Anthropology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AHSN",
                                "description": "Arabic & Hebrew Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AISN",
                                "description": "Arabic & Islamic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CAAM",
                                "description": "Archaeological Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARCH",
                                "description": "Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ASAM",
                                "description": "Asian American Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOE",
                                "description": "Bioethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOL",
                                "description": "Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOP",
                                "description": "Biophysics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CBE",
                                "description": "Chemical & Biomolecular Eng",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CHEM",
                                "description": "Chemistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CIMS",
                                "description": "Cinema and Media Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CLST",
                                "description": "Classical Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "COGS",
                                "description": "Cognitive Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CMPL",
                                "description": "Comparative Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CNSC",
                                "description": "Computational Neuroscience",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CSCI",
                                "description": "Computer Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CNPS",
                                "description": "Consumer Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DATS",
                                "description": "Data Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DSGN",
                                "description": "Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DHUM",
                                "description": "Digital Humanities",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DMD",
                                "description": "Digital Media Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EAST",
                                "description": "East Asian Area Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALJ",
                                "description": "East Asian Lang  Civil/Jpn",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALN",
                                "description": "East Asian Lang & Civil/Chns",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALK",
                                "description": "East Asian Lang & Civil/Korean",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ECES",
                                "description": "East Central European Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EPOL",
                                "description": "Economic Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ECON",
                                "description": "Economics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EE",
                                "description": "Electrical Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENSU",
                                "description": "Energy & Sustainability",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EENT",
                                "description": "Engineering Entrepreneurship",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENGL",
                                "description": "English",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENVH",
                                "description": "Environmental Humanities",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EVSC",
                                "description": "Environmental Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENVS",
                                "description": "Environmental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EURO",
                                "description": "European Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FNAR",
                                "description": "Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FRFS",
                                "description": "French and Francophone Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GSWS",
                                "description": "Gen, Sexuality & Women's Sts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GEOL",
                                "description": "Geology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GRMN",
                                "description": "German",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GMST",
                                "description": "Global Medieval Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HEBN",
                                "description": "Hebrew & Judaica",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HSPN",
                                "description": "Hispanic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HIST",
                                "description": "History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARTH",
                                "description": "History of Art",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSCD",
                                "description": "International Development",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "INTR",
                                "description": "International Relations",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ITCL",
                                "description": "Italian Culture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ITLT",
                                "description": "Italian Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JAZZ",
                                "description": "Jazz & Popular Music Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JWST",
                                "description": "Jewish Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JRNL",
                                "description": "Journalistic Writing",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LANS",
                                "description": "Landscape Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LALX",
                                "description": "Latin American and Latinx Stds",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LAWS",
                                "description": "Law and Society",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LSHS",
                                "description": "Legal Studies & History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LING",
                                "description": "Linguistics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LGIC",
                                "description": "Logic Info  & Computation",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSE",
                                "description": "Materials Science & Engin",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MATH",
                                "description": "Mathematics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MEAM",
                                "description": "Mech Engr & Appl Mechanics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSOC",
                                "description": "Medical Sociology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ATCH",
                                "description": "Minor In Architectural History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MMES",
                                "description": "Modern Middle Eastern Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MUSC",
                                "description": "Music",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NAIS",
                                "description": "Native American And Indigenous",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NRSC",
                                "description": "Neuroscience",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NONE",
                                "description": "Non Designated",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NHSM",
                                "description": "Nursing & Hlth Services Mgmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NUTR",
                                "description": "Nutrition",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "APEN",
                                "description": "Persian Language & Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHIL",
                                "description": "Philosophy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHYS",
                                "description": "Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSCI",
                                "description": "Political Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSYS",
                                "description": "Psychoanalytic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSYC",
                                "description": "Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RELS",
                                "description": "Religious Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RULA",
                                "description": "Russ Lang.,Lit.,&Culture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RUCH",
                                "description": "Russian Culture & History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "STSC",
                                "description": "Science Technology & Society",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SOCI",
                                "description": "Sociology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SAST",
                                "description": "South Asia Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SRDA",
                                "description": "Survey Res & Data Analytics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SEVM",
                                "description": "Sustainability & Envl Mgmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SSE",
                                "description": "Systems Science & Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "THAR",
                                "description": "Theatre Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URED",
                                "description": "Urban Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URRE",
                                "description": "Urban Real Estate & Dvpmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URBS",
                                "description": "Urban Studies",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": [],
                        "ruleGoalCode": "MINOR",
                        "links": [],
                    },
                ],
            },
            {
                "id": "secondaryCurriculumCollection",
                "description": "Additional areas of study",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "secondaryProgram",
                        "description": "Program",
                        "entityName": "programs",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/programs",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [
                            {
                                "key": "AU_BA_BIOD_U",
                                "description": "*Seven Yr Bio-Dent Pgrm Pre-Maj",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA",
                                "description": "Arts & Sciences - BA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_UNDC",
                                "description": "Arts & Sciences - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_CMPC_U",
                                "description": "Dual Degree - Computer & Cog Sci - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_HUNTS",
                                "description": "Dual Degree - Huntsman - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_HUNTS",
                                "description": "Dual Degree - Huntsman - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_MANT",
                                "description": "Dual Degree - M & T - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MANT",
                                "description": "Dual Degree - M & T - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MAT_U",
                                "description": "Dual Degree - M & T - BS - Wharton (Pre-Conc)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MAT_U",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MANT",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BSN - Nursing",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPR_U",
                                "description": "Dual Degree - VIPER - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPER",
                                "description": "Dual Degree - VIPER - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_VIPER",
                                "description": "Dual Degree - VIPER - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIPER",
                                "description": "Dual Degree - VIPER - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIP_U",
                                "description": "Dual Degree - VIPER - BSE - SEAS - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton-Pre-Conc",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_BAAS_ONL",
                                "description": "LPS - Bachelor of Applied Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_BFA",
                                "description": "LPS - Bachelor of Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CERTA_OL",
                                "description": "LPS - Certificate (Undergraduate Advanced Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_CERTF_UG",
                                "description": "LPS - Certificate (Undergraduate FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CRT_UG_OL",
                                "description": "LPS - Certificate (Undergraduate Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN",
                                "description": "Nursing - BSN",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NAP",
                                "description": "Nursing - BSN (Accelerated)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE",
                                "description": "SEAS - BSE",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_CD",
                                "description": "SEAS - BSE - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS",
                                "description": "SEAS - Bachelor of Applied Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_CD",
                                "description": "SEAS - Bachelor of Applied Science - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS",
                                "description": "Wharton - BS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_WUNG",
                                "description": "Wharton - BS - Pre Concentration",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": [],
                        "ruleGoalCode": "PROGRAM",
                        "links": [],
                    },
                    {
                        "name": "secondaryCollege",
                        "description": "College",
                        "entityName": "colleges",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/colleges",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "secondaryDegree",
                        "description": "Degree",
                        "entityName": "degrees",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/degrees",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "secondaryMajor",
                        "description": "Major",
                        "entityName": "majors",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/majors-whatif",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "secondaryConcentration",
                        "description": "Concentration",
                        "entityName": "concentrations",
                        "isDisabled": True,
                        "isDriver": False,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/concentrations",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "secondaryMinor",
                        "description": "Minor",
                        "entityName": "minors",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/validations/special-entities/minors-whatif",
                        "errorMessage": "",
                        "catalogYear": "",
                        "choices": [],
                        "selectedChoices": [],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                ],
            },
        ]

        found_degrees: list[Degree] = []
        # set program
        goals_payload[0]["goals"][1]["selectedChoices"] = [program_code]

        res = self.s.post(
            f"{BASE_URL}/api/goals",
            json=goals_payload,
        )

        # LEVEL
        levels = res.json()[0]["goals"][2]["choices"]
        if undergrad_only and len([choice for choice in levels if choice["key"] == "UG"]) < 1:
            print("No undergraduate degree for program", program_code)
            return []
        goals_payload[0]["goals"][2]["selectedChoices"] = ["UG"]

        # DEGREE
        degrees = res.json()[0]["goals"][4]["choices"]
        for degree in degrees:
            degree_code = degree["key"]
            if undergrad_only:
                assert degree_code.startswith("B")  # i.e., is a bachelor's degree

            # set degree
            goals_payload[0]["goals"][4]["selectedChoices"] = [degree_code]

            res = self.s.post(
                f"{BASE_URL}/api/goals",
                json=goals_payload,
            )

            majors = res.json()[1]["goals"][0]["choices"]

            # MAJOR
            for major in majors:
                major_code = major["key"]
                major_name = major["description"]
                goals_payload[1]["goals"][0]["selectedChoices"] = [major_code]

                res = self.s.post(
                    f"{BASE_URL}/api/goals",
                    json=goals_payload,
                )

                # CONCENTRATION
                concentrations = res.json()[1]["goals"][1]["choices"]
                if len(concentrations) == 0:
                    found_degrees.append(
                        Degree(
                            program=program_code,
                            degree=degree_code,
                            major=major_code,
                            major_name=major_name,
                            concentration=None,
                            concentration_name=None,
                            year=year,
                        )
                    )
                    continue
                for concentration in concentrations:
                    concentration_code = concentration["key"]
                    concentration_name = concentration["description"]
                    found_degrees.append(
                        Degree(
                            program=program_code,
                            degree=degree_code,
                            major=major_code,
                            major_name=major_name,
                            concentration=concentration_code,
                            concentration_name=concentration_name,
                            year=year,
                        )
                    )

        return found_degrees

    def get_programs(self, timeout=30, year: int = 2023) -> str:
        goals_payload = [
            {
                "id": "programCollection",
                "description": "Program",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "catalogYear",
                        "description": "Catalog year",
                        "entityName": "catalogYears",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": True,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "api/catalogYears",
                        "errorMessage": "",
                        "choices": [],
                        "selectedChoices": [str(year)],
                        "ruleGoalCode": None,
                        "links": [],
                    },
                    {
                        "name": "program",
                        "description": "Program",
                        "entityName": "programs",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "NP_PHD_JOINT",
                                "description": "*Nursing Joint PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_BIOD_U",
                                "description": "*Seven Yr Bio-Dent Pgrm Pre-Maj",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CP_MA",
                                "description": "Annenberg - MA (PhD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CP_PHD",
                                "description": "Annenberg - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA",
                                "description": "Arts & Sciences - BA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_UNDC",
                                "description": "Arts & Sciences - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_PHD_JOINT",
                                "description": "Arts & Sciences - Joint PhD Degree",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MA",
                                "description": "Arts & Sciences - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MPHIL",
                                "description": "Arts & Sciences - MPhil",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MS",
                                "description": "Arts & Sciences - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_PHD",
                                "description": "Arts & Sciences - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_CERTF_DM",
                                "description": "Dental - Certificate (Post-Graduate FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_CERT_DM",
                                "description": "Dental - Certificate (Post-Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD",
                                "description": "Dental - Doctor of Dental Medicine",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD_BIOD",
                                "description": "Dental - Doctor of Dental Medicine (7-yr)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DM_DMD_PASS",
                                "description": "Dental - Doctor of Dental Medicine (Advanced)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_DSCD",
                                "description": "Dental - Doctor of Science in Dentistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MADS",
                                "description": "Dental - Master of Advance Dental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MOHS",
                                "description": "Dental - Master of Oral Health Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DY_MSOB",
                                "description": "Dental - Master of Science in Oral Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_CERT_GR",
                                "description": "Design - Certificate (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_CERT_PR",
                                "description": "Design - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_MA",
                                "description": "Design - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_MS",
                                "description": "Design - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MARCH",
                                "description": "Design - Master of Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MCP",
                                "description": "Design - Master of City Planning",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MEBD",
                                "description": "Design - Master of Environmental Building Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MFA",
                                "description": "Design - Master of Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MLA",
                                "description": "Design - Master of Landscape Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MSDES",
                                "description": "Design - Master of Science in Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MSHP",
                                "description": "Design - Master of Science in Historic Preserv",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FM_MUSA",
                                "description": "Design - Master of Urban Spatial Analytics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FP_PHD",
                                "description": "Design - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_CMPC_U",
                                "description": "Dual Degree - Computer & Cog Sci - BA - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_HUNTS",
                                "description": "Dual Degree - Huntsman - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_HUNTS",
                                "description": "Dual Degree - Huntsman - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AP_MA_LAUD",
                                "description": "Dual Degree - Lauder - MA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_LAUD",
                                "description": "Dual Degree - Lauder - MBA - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_MANT",
                                "description": "Dual Degree - M & T - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MANT",
                                "description": "Dual Degree - M & T - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_MAT_U",
                                "description": "Dual Degree - M & T - BS - Wharton (Pre-Conc)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MANT",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_MAT_U",
                                "description": "Dual Degree - M & T - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NHCM",
                                "description": "Dual Degree - Nursing & HC Mgmt - BSN - Nursing",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPR_U",
                                "description": "Dual Degree - VIPER - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VIPER",
                                "description": "Dual Degree - VIPER - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_VIPER",
                                "description": "Dual Degree - VIPER - BAS - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIPER",
                                "description": "Dual Degree - VIPER - BSE - SEAS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_VIP_U",
                                "description": "Dual Degree - VIPER - BSE - SEAS - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BA - A & S - Pre-Major",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AU_BA_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BA - Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_VAGL_U",
                                "description": "Dual Degree - Vagelos LSM - BS - Wharton-Pre-Conc",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_CE",
                                "description": "GSE - Certificate (Continuing Ed.)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_ONL",
                                "description": "GSE - Certificate (Online Continuing Ed.)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERT_PR",
                                "description": "GSE - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_CERT_GR",
                                "description": "GSE - Certificate (Research)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_CERTF_PR",
                                "description": "GSE - Certificate - UTRP/Sch Leadership (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_EDD",
                                "description": "GSE - Doctor of Education (EdD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MSED",
                                "description": "GSE - MS in Education (MSEd)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MSED_ONL",
                                "description": "GSE - MS in Education - Online (MSED)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GM_MPHILE",
                                "description": "GSE - Master of Philosophy in Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_PHD",
                                "description": "GSE - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_PHD_JOINT",
                                "description": "GSE Joint Phd",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_MSED",
                                "description": "GSE Master of Sci in Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GP_MS",
                                "description": "GSE Master of Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LR_JD_JDMBA",
                                "description": "LAW JD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_BAAS_ONL",
                                "description": "LPS - Bachelor of Applied Arts & Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_BFA",
                                "description": "LPS - Bachelor of Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_CERTF_PR",
                                "description": "LPS - Certificate (Professional FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_CERT_PR",
                                "description": "LPS - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CERTA_OL",
                                "description": "LPS - Certificate (Undergraduate Advanced Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AL_CERTF_UG",
                                "description": "LPS - Certificate (Undergraduate FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AB_CRT_UG_OL",
                                "description": "LPS - Certificate (Undergraduate Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MPHIL",
                                "description": "LPS - MPhil",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSAG",
                                "description": "LPS - MS in Applied Geosciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSOD",
                                "description": "LPS - MS in Organizational Dynamics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MAPP",
                                "description": "LPS - Master of Applied Positive Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MBDS",
                                "description": "LPS - Master of Behavioral & Decision Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MCS",
                                "description": "LPS - Master of Chemical Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MES",
                                "description": "LPS - Master of Environmental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MLIBA",
                                "description": "LPS - Master of Liberal Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MPA",
                                "description": "LPS - Master of Public Administration",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AM_MSAG_ONL",
                                "description": "LPS MS in Appl Geosci Online",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_CERT",
                                "description": "Law - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LD_SJD",
                                "description": "Law - Doctorate of the Science of Law (SJD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LR_JD",
                                "description": "Law - Juris Doctor (JD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_MLAW",
                                "description": "Law - Master in Law (ML)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_LLM",
                                "description": "Law - Master of Laws (LLM)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LY_LLCM",
                                "description": "Law - Masters in Comparative Law (LLCM)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_CERT_GR",
                                "description": "Medicine - Certificate (Graduate)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERT_ONL",
                                "description": "Medicine - Certificate (Online Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERTF_PR",
                                "description": "Medicine - Certificate (Professional FinAid)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_CERT_PR",
                                "description": "Medicine - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MR_MD",
                                "description": "Medicine - MD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_MS",
                                "description": "Medicine - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MBE",
                                "description": "Medicine - Master of Bioethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MBMI",
                                "description": "Medicine - Master of Biomedical Informatics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MHCI_ONL",
                                "description": "Medicine - Master of Health Care Innovation",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MHQS",
                                "description": "Medicine - Master of Healthcare Quality and Safety",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MPH",
                                "description": "Medicine - Master of Public Health",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MRA",
                                "description": "Medicine - Master of Regulatory Affairs",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MRA_ONL",
                                "description": "Medicine - Master of Regulatory Affairs (ONL)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSCE",
                                "description": "Medicine - Master of Science in Clin Epidemiology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSGC",
                                "description": "Medicine - Master of Science in Genetic Counseling",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MPR",
                                "description": "Medicine - Master of Science in Health Pol Resrch",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSME",
                                "description": "Medicine - Master of Science in Medical Ethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSMP",
                                "description": "Medicine - Master of Science in Medical Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSRS",
                                "description": "Medicine - Master of Science in Regulatory Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MM_MSTR",
                                "description": "Medicine - Master of Science in Translatnal Resrch",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD",
                                "description": "Medicine - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN",
                                "description": "Nursing - BSN",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NU_BSN_NAP",
                                "description": "Nursing - BSN (Accelerated)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_PMN",
                                "description": "Nursing - Certificate (Post-Masters)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_CERT_PR",
                                "description": "Nursing - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ND_DNP",
                                "description": "Nursing - Doctor of Nursing Practice",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ND_DNP_ONL",
                                "description": "Nursing - Doctor of Nursing Practice (Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NP_MS",
                                "description": "Nursing - MS (PhD)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NM_MSN",
                                "description": "Nursing - MSN",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NP_PHD",
                                "description": "Nursing - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD_MDPHD",
                                "description": "PSOM Doctor of Philosophy/MD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MP_PHD_VRPHD",
                                "description": "PSOM Doctor of Philosophy/VMD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE",
                                "description": "SEAS - BSE",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BSE_CD",
                                "description": "SEAS - BSE - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS",
                                "description": "SEAS - Bachelor of Applied Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EU_BAS_CD",
                                "description": "SEAS - Bachelor of Applied Science - Curric Defer",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EX_MSE",
                                "description": "SEAS - Executive MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MCIT",
                                "description": "SEAS - MCIT (On Campus)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MCIT_ONL",
                                "description": "SEAS - MCIT (Online)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MSE",
                                "description": "SEAS - MSE",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MBIOT",
                                "description": "SEAS - Master of Biotechnology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EM_MIPD",
                                "description": "SEAS - Master of Intg Prod Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EP_PHD",
                                "description": "SEAS - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SP_PHD_JOINT",
                                "description": "SP2 Joint Phd",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSNPL",
                                "description": "Social Policy & Prac - MS in Non-Profit Leadership",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSNPL_ONL",
                                "description": "Social Policy & Prac - MS in Non-Profit Leadership",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SD_DSW_ONL",
                                "description": "Social Policy & Practice - Doctor of Social Work",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSSP",
                                "description": "Social Policy & Practice - MS in Social Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SM_MSW",
                                "description": "Social Policy & Practice - Master of Social Work",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SP_PHD",
                                "description": "Social Policy & Practice - PhD in Social Welfare",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VM_MSAWB_ONL",
                                "description": "VET Mstr of Sci Ani Wlfr Bhvr",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VM_CERT_ONL",
                                "description": "Vet - Certificate (Professional)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VR_VMD",
                                "description": "Vet - PhD/Doctor of Veterinary Medicine",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VP_VMD",
                                "description": "Vet - Veterinariae Medicinae Doctoris-VMD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_JDMBA",
                                "description": "WH JD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EBMBA",
                                "description": "WH MBA/MBIOT",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_ECMBA",
                                "description": "WH MBA/MCIT",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_FMMBA",
                                "description": "WH MBA/MFA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EIMBA",
                                "description": "WH MBA/MIPD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_EMMBA",
                                "description": "WH MBA/MSEng",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_MDMBA",
                                "description": "WH MD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA_VRMBA",
                                "description": "WH VMD/MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS",
                                "description": "Wharton - BS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WX_MBA_PHL",
                                "description": "Wharton - Executive MBA (Philadelphia)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WX_MBA_SFO",
                                "description": "Wharton - Executive MBA (San Francisco)",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_PHD_JOINT",
                                "description": "Wharton - Joint PhD Degree",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_MA",
                                "description": "Wharton - MA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WM_MBA",
                                "description": "Wharton - MBA",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_MS",
                                "description": "Wharton - MS",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WP_PHD",
                                "description": "Wharton - PhD",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WU_BS_WUNG",
                                "description": "Wharton - Pre Concentration (Undergraduate)",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": ["EU_BSE"],
                        "ruleGoalCode": "PROGRAM",
                        "links": [],
                    },
                    {
                        "name": "school",
                        "description": "Level",
                        "entityName": "schools",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "UG",
                                "description": "Undergraduate",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["UG"],
                        "ruleGoalCode": "SCHOOL",
                        "links": [],
                    },
                    {
                        "name": "college",
                        "description": "College",
                        "entityName": "colleges",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "EU",
                                "description": "SEAS Undergraduate",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["EU"],
                        "ruleGoalCode": "COLLEGE",
                        "links": [],
                    },
                    {
                        "name": "degree",
                        "description": "Degree",
                        "entityName": "degrees",
                        "isDisabled": True,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "BSE",
                                "description": "Bachelor of Sci in Engineering",
                                "isVisibleInWhatif": True,
                            }
                        ],
                        "selectedChoices": ["BSE"],
                        "ruleGoalCode": "DEGREE",
                        "links": [],
                    },
                ],
            },
            {
                "id": "curriculumCollection",
                "description": "Areas of study",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "major",
                        "description": "Major",
                        "entityName": "majors",
                        "isDisabled": False,
                        "isDriver": True,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": True,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "AFRC",
                                "description": "Africana Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANCH",
                                "description": "Ancient History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANTH",
                                "description": "Anthropology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARCH",
                                "description": "Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BCHE",
                                "description": "Biochemistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BE",
                                "description": "Bioengineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOL",
                                "description": "Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOP",
                                "description": "Biophysics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CBSC",
                                "description": "Chem & Biomolecular Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CBE",
                                "description": "Chemical & Biomolecular Eng",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CHEM",
                                "description": "Chemistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CIMS",
                                "description": "Cinema and Media Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CLST",
                                "description": "Classical Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "COGS",
                                "description": "Cognitive Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "COMM",
                                "description": "Communication",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CMPL",
                                "description": "Comparative Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CMPE",
                                "description": "Computer Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CSCI",
                                "description": "Computer Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CRIM",
                                "description": "Criminology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DSGN",
                                "description": "Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DMD",
                                "description": "Digital Media Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EASC",
                                "description": "Earth Sciences",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALC",
                                "description": "East Asian Lang & Civilization",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ECOQ",
                                "description": "Economics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EE",
                                "description": "Electrical Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENGL",
                                "description": "English",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENVS",
                                "description": "Environmental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FNAR",
                                "description": "Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FRFS",
                                "description": "French and Francophone Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GSWS",
                                "description": "Gen, Sexuality & Womens Sts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GRMN",
                                "description": "German",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HSOC",
                                "description": "Health and Societies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HSPN",
                                "description": "Hispanic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HIST",
                                "description": "History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARTH",
                                "description": "History of Art",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "INDM",
                                "description": "Individualized",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "INTR",
                                "description": "International Relations",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ITST",
                                "description": "Italian Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JWST",
                                "description": "Jewish Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LALX",
                                "description": "Latin American and Latinx Stds - LALX",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LING",
                                "description": "Linguistics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LOGC",
                                "description": "Logic Info  & Computation",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSE",
                                "description": "Materials Science & Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MAEC",
                                "description": "Mathematical Economics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MATH",
                                "description": "Mathematics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MEAM",
                                "description": "Mech Engr & Appl Mechanics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MMES",
                                "description": "Modern Middle Eastern Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MUSC",
                                "description": "Music",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NELC",
                                "description": "Near Eastern Lang & Civilizatn",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NETS",
                                "description": "Networked And Social Systems",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NRSC",
                                "description": "Neuroscience",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NTSC",
                                "description": "Nutrition Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHIL",
                                "description": "Philosophy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PPE",
                                "description": "Philosophy Politics & Econ",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHYS",
                                "description": "Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSCI",
                                "description": "Political Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSYC",
                                "description": "Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RELS",
                                "description": "Religious Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ROML",
                                "description": "Romance Languages",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "REES",
                                "description": "Russian& East European Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "STSC",
                                "description": "Science Technology & Society",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SOCI",
                                "description": "Sociology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SAST",
                                "description": "South Asia Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SSE",
                                "description": "Systems Science & Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "THAR",
                                "description": "Theatre Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URBS",
                                "description": "Urban Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "VLST",
                                "description": "Visual Studies",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": ["BE"],
                        "ruleGoalCode": "MAJOR",
                        "links": [],
                    },
                    {
                        "name": "concentration",
                        "description": "Concentration",
                        "entityName": "concentrations",
                        "isDisabled": False,
                        "isDriver": False,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "BDS",
                                "description": "Biomed Data Sci&Cmptationl Med",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIR",
                                "description": "Biomed Imgng&Radiation Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BDV",
                                "description": "Biomedical Devices",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CEB",
                                "description": "Cellular/Tissue Engin & Biomat",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSB",
                                "description": "Multiscale Biomechanics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NRE",
                                "description": "Neuroengineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NONE",
                                "description": "Non Designated",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SSB",
                                "description": "Systems and Synthetic Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "TDN",
                                "description": "Therapeutics,Drug Dliv&Nanomed",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": [],
                        "ruleGoalCode": "CONC",
                        "links": [],
                    },
                    {
                        "name": "minor",
                        "description": "Minor",
                        "entityName": "minors",
                        "isDisabled": False,
                        "isDriver": False,
                        "isError": False,
                        "isMultiple": False,
                        "isRequired": False,
                        "isStatic": False,
                        "isVisible": True,
                        "isNoValidOptionsWarning": False,
                        "source": "",
                        "errorMessage": "",
                        "choices": [
                            {
                                "key": "ACRL",
                                "description": "Actuarial Mathematics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AFRC",
                                "description": "Africana Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AMPP",
                                "description": "American Public Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ASL",
                                "description": "American Sign Lang/Deaf Stds",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANCH",
                                "description": "Ancient History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANEN",
                                "description": "Ancient Near East",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ANTH",
                                "description": "Anthropology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AHSN",
                                "description": "Arabic & Hebrew Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "AISN",
                                "description": "Arabic & Islamic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CAAM",
                                "description": "Archaeological Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARCH",
                                "description": "Architecture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ASAM",
                                "description": "Asian American Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOE",
                                "description": "Bioethics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOL",
                                "description": "Biology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "BIOP",
                                "description": "Biophysics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CBE",
                                "description": "Chemical & Biomolecular Eng",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CHEM",
                                "description": "Chemistry",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CIMS",
                                "description": "Cinema and Media Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CLST",
                                "description": "Classical Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "COGS",
                                "description": "Cognitive Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CMPL",
                                "description": "Comparative Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CNSC",
                                "description": "Computational Neuroscience",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CSCI",
                                "description": "Computer Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "CNPS",
                                "description": "Consumer Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DATS",
                                "description": "Data Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DSGN",
                                "description": "Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DHUM",
                                "description": "Digital Humanities",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "DMD",
                                "description": "Digital Media Design",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EAST",
                                "description": "East Asian Area Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALJ",
                                "description": "East Asian Lang  Civil/Jpn",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALN",
                                "description": "East Asian Lang & Civil/Chns",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EALK",
                                "description": "East Asian Lang & Civil/Korean",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ECES",
                                "description": "East Central European Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EPOL",
                                "description": "Economic Policy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ECON",
                                "description": "Economics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EE",
                                "description": "Electrical Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENSU",
                                "description": "Energy & Sustainability",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EENT",
                                "description": "Engineering Entrepreneurship",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENGL",
                                "description": "English",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENVH",
                                "description": "Environmental Humanities",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EVSC",
                                "description": "Environmental Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ENVS",
                                "description": "Environmental Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "EURO",
                                "description": "European Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FNAR",
                                "description": "Fine Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "FRFS",
                                "description": "French and Francophone Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GSWS",
                                "description": "Gen, Sexuality & Women's Sts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GEOL",
                                "description": "Geology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GRMN",
                                "description": "German",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "GMST",
                                "description": "Global Medieval Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HEBN",
                                "description": "Hebrew & Judaica",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HSPN",
                                "description": "Hispanic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "HIST",
                                "description": "History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ARTH",
                                "description": "History of Art",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSCD",
                                "description": "International Development",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "INTR",
                                "description": "International Relations",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ITCL",
                                "description": "Italian Culture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ITLT",
                                "description": "Italian Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JAZZ",
                                "description": "Jazz & Popular Music Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JWST",
                                "description": "Jewish Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "JRNL",
                                "description": "Journalistic Writing",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LANS",
                                "description": "Landscape Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LALX",
                                "description": "Latin American and Latinx Stds",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LAWS",
                                "description": "Law and Society",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LSHS",
                                "description": "Legal Studies & History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LING",
                                "description": "Linguistics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "LOGC",
                                "description": "Logic Info & Computation",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSE",
                                "description": "Materials Science & Engin",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MATH",
                                "description": "Mathematics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MEAM",
                                "description": "Mech Engr & Appl Mechanics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MSOC",
                                "description": "Medical Sociology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ATCH",
                                "description": "Minor In Architectural History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MMES",
                                "description": "Modern Middle Eastern Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "MUSC",
                                "description": "Music",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NANO",
                                "description": "Nanotechnology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NAIS",
                                "description": "Native American And Indigenous",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NELC",
                                "description": "Near Eastern Lang & Civilizatn",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NHMG",
                                "description": "Neurosci & Health Care Mgmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NRSC",
                                "description": "Neuroscience",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NHSM",
                                "description": "Nursing & Hlth Services Mgmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "NUTR",
                                "description": "Nutrition",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "APEN",
                                "description": "Persian Language & Literature",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHIL",
                                "description": "Philosophy",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PHYS",
                                "description": "Physics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSCI",
                                "description": "Political Science",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSYS",
                                "description": "Psychoanalytic Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "PSYC",
                                "description": "Psychology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RELS",
                                "description": "Religious Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "ROML",
                                "description": "Romance Languages",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RULA",
                                "description": "Russ Lang.,Lit.,&Culture",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "RUCH",
                                "description": "Russian Culture & History",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "STSC",
                                "description": "Science Technology & Society",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SOCI",
                                "description": "Sociology",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SARS",
                                "description": "South Asia Regional Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SAST",
                                "description": "South Asia Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SPAN",
                                "description": "Spanish",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "STAT",
                                "description": "Statistics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SRDA",
                                "description": "Survey Res & Data Analytics",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SEVM",
                                "description": "Sustainability & Envl Mgmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SE",
                                "description": "Systems Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "SSE",
                                "description": "Systems Science & Engineering",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "THAR",
                                "description": "Theatre Arts",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URED",
                                "description": "Urban Education",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URRE",
                                "description": "Urban Real Estate & Dvpmt",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "URBS",
                                "description": "Urban Studies",
                                "isVisibleInWhatif": True,
                            },
                            {
                                "key": "WSTD",
                                "description": "Womens Studies",
                                "isVisibleInWhatif": True,
                            },
                        ],
                        "selectedChoices": ["AHSN"],
                        "ruleGoalCode": "MINOR",
                        "links": [],
                    },
                ],
            },
            {
                "id": "secondaryCurriculumCollection",
                "description": "Additional areas of study",
                "isExpandable": False,
                "goals": [
                    {
                        "name": "secondaryProgram",
                        "description": "Program",
                        "selectedChoices": [],
                        "choices": [],
                    },
                    {
                        "name": "secondaryCollege",
                        "description": "College",
                        "choices": [],
                        "selectedChoices": [],
                    },
                    {
                        "name": "secondaryDegree",
                        "description": "Degree",
                        "choices": [],
                        "selectedChoices": [],
                    },
                    {
                        "name": "secondaryMajor",
                        "description": "Major",
                        "choices": [],
                        "selectedChoices": [],
                    },
                    {
                        "name": "secondaryConcentration",
                        "description": "Concentration",
                        "choices": [],
                        "selectedChoices": [],
                    },
                    {
                        "name": "secondaryMinor",
                        "description": "Minor",
                        "choices": [],
                        "selectedChoices": [],
                    },
                ],
            },
        ]
        res = self.s.post(
            f"{BASE_URL}/api/goals",
            json=goals_payload,
            timeout=timeout,
        )
        res.raise_for_status()

        return [program["key"] for program in res.json()[0]["goals"][1]["choices"]]


def write_dp(dp: Degree, audit_json: dict, dir: str | Path = "degrees", overwrite=False):
    file_name = f"{dp.year}-{dp.program}-{dp.degree}-{dp.major}"
    if dp.concentration is not None:
        file_name += f"-{dp.concentration}"
    Path(dir).mkdir(
        exist_ok=True,
        parents=True,  # will still throw an error if dir is a non-directory file
    )
    file_path = Path(dir, file_name)
    if not overwrite and file_path.exists():
        raise FileExistsError(f"Degree with path `{file_name}`")

    with open(file_path, "w") as f:
        json.dump(audit_json, f, indent=4)
