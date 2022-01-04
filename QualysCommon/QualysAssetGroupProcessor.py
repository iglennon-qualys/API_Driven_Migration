import xml.etree.ElementTree as ET
from QualysCommon import QualysAPI


def responseHandler(response: ET.Element):
    if response.find('.//CODE') is None:
        return True
    else:
        print('ERROR %s: %s' % (response.find('.//CODE').text, response.find('.//TEXT').text))
        return False


def getAssetGroups(source_api: QualysAPI.QualysAPI):
    fullurl = '%s/api/2.0/fo/asset/group/?action=list&show_attributes=ALL' % source_api.server
    resp = source_api.makeCall(url=fullurl)

    if not responseHandler(resp):
        return None

    usesnetworks = False
    aglist = resp.find('.//ASSET_GROUP_LIST')
    return aglist


def convertAssetGroups(aglist: ET.Element, netmap: dict = None, appliancemap: dict = None):
    # Takes the XML generated by getAssetGroups(), updates the Network, Appliance and Domain information from the
    # corresponding maps and returns a list of URLs to recreate those Asset Groups
    urllist = []
    baseurl = '/api/2.0/fo/asset/group/?action=add'

    for ag in aglist.findall('.//ASSET_GROUP'):
        if ag.find('TITLE').text == 'All':
            continue
        addurl = '%s&title=%s' % (baseurl, ag.find('TITLE').text)

        if ag.find('CVSS_ENVIRO_CDP').text != "Not Defined":
            addurl = '%s&cvss_enviro_cdp=%s' % (addurl, ag.find('CVSS_ENVIRO_CDP').text.lower())

        if ag.find('CVSS_ENVIRO_TD').text != "Not Defined":
            addurl = '%s&cvss_enviro_td=%s' % (addurl, ag.find('CVSS_ENVIRO_TD').text.lower())

        if ag.find('CVSS_ENVIRO_CR').text != "Not Defined":
            addurl = '%s&cvss_enviro_cr=%s' % (addurl, ag.find('CVSS_ENVIRO_CR').text.lower())

        if ag.find('CVSS_ENVIRO_IR').text != "Not Defined":
            addurl = '%s&cvss_enviro_ir=%s' % (addurl, ag.find('CVSS_ENVIRO_IR').text.lower())

        if ag.find('CVSS_ENVIRO_AR').text != "Not Defined":
            addurl = '%s&cvss_enviro_ar=%s' % (addurl, ag.find('CVSS_ENVIRO_AR').text.lower())

        if ag.find('COMMENTS') is not None:
            addurl = '%s&comments=%s' % (addurl, ag.find('COMMENTS').text)

        if ag.find('IP_SET') is not None:
            ipset = ag.find('IP_SET')
            ips = []
            for iprange in ipset.findall('*'):
                ips.append(iprange.text)
            addurl = '%s&ips=%s' % (addurl, ','.join(ips))

        if ag.find('DOMAIN_LIST') is not None:
            dlist = ag.find('DOMAIN_LIST')
            domains = []
            for domain in dlist.findall('DOMAIN'):
                domains.append('%s:[%s]' % (domain.text, domain.get('netblock')))
            addurl = '%s&domains=%s' % (addurl, ','.join(domains))

        if ag.find('DNS_LIST') is not None:
            dnslist = ag.find('DNS_LIST')
            dnsnames = []
            for dnsname in dnslist.findall('DNS'):
                dnsnames.append('%s' % dnsname.text)
            addurl = '%s&dns_names=%s' % (addurl, ','.join(dnsnames))

        if ag.find('NETBIOS_LIST') is not None:
            netbioslist = ag.find('NETBIOS_LIST')
            netbiosnames = []
            for netbiosname in netbioslist.findall('NETBIOS'):
                netbiosnames.append('%s' % netbiosname.text)
            addurl = '%s&netbios_names=%s' % (addurl, ','.join(netbiosnames))

        if ag.find('NETWORK_ID') is not None:
            if not ag.find('NETWORK_ID').text == '0':
                if netmap is None:
                    print('FATAL: Asset Group %s is assigned to a non-zero Network object but network map is not '
                          'provided or is empty' % ag.find('TITLE').text)
                    return None
                newnetid = netmap[ag.find('NETWORK_ID').text]
                addurl = '%s&network_id=%s' % (addurl, newnetid)

        if ag.find('DEFAULT_APPLIANCE_ID') is not None:
            if appliancemap is None:
                print('FATAL: Asset Group %s has scanner appliances assigned but no appliance map is provided' %
                      ag.find('TITLE').text)
                return None
            newapp = appliancemap[ag.find('DEFAULT_APPLIANCE_ID').text]
            addurl = '%s&default_appliance_id=%s' % (addurl, newapp)

        if ag.find('APPLIANCE_IDS') is not None:
            if appliancemap is None:
                print('FATAL: Asset Group %s has scanner appliances assigned but no appliance map is provided' %
                      ag.find('TITLE').text)
                return None
            addurl = '%s&appliance_ids=%s' % (addurl, ag.find('APPLIANCE_IDS').text)

        urllist.append(addurl)
    return urllist


def createAssetGroups(target_api: QualysAPI.QualysAPI, urllist: list):
    for url in urllist:
        fullurl = '%s%s' % (target_api.server, url)
        resp = target_api.makeCall(url=fullurl)
        if not responseHandler(resp):
            print('FATAL: Could not create Asset Group')
            return False
    return True
