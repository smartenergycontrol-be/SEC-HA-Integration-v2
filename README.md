# Home Assistant smartenergycontrol.be component

Custom component for Home Assistant to calculate hourly prices for all Belgian energy contracts on the market (fixed, flexible and dynamic)



### Sensors
cunsuption and injections prices for all contracts in the Vreg V-test datasource. Hourly today and hourly next day when available trought the entso-e API. Also a sensor that holds all distributor and government parameters for electricty price calculation.
  
------
## Installation


### Manual
Download this repository and place the contents of `custom_components` in your own `custom_components` map of your Home Assistant installation. Restart Home Assistant and add the integration through your settings. 

### HACS

Add ths repo https://github.com/smartenergycontrol-be/SEC-HA-Integration-v2 to your custom repo's in HACS.
Search for "Smartenergycontrol" and add the HACS integrations. Restart Home Assistant and add the integration through your settings or use the button below to add the repo and click download.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=https://github.com/smartenergycontrol-be&repository=SEC-HA-Integration-v2&category=integration)

------
## Configuration and use

You can choose your current contract en energy distributer trough postal code using the web UI. 

The integration will ask for your postal code (all Belgian postcodes supported) and an API key ([contact me](mailto:steven@smartenergycontrol.be) if you want access).
The integration will get up-to-date distribution tarifs for Belgium (taxes, accijnzen, groene stoom WWK, capaciteits tarief etc) depending on where you live. You will be able to add all the existing Enegy contracts (fixed, flible and dynamic) that exist in the V-test from VREG (updated monthly). Add your contract, select it as current, and select a nummber of other contracts from te list to compare.
See your real daily electricity cost with your existing contract and compare with other contracts or formulas out there.

------

#### Updates

The integration is in an early state and receives a lot of updates. If you already setup this integration and encounter an error after updating, please try redoing the above installation steps. 

#### Usage
![image](https://github.com/user-attachments/assets/4af69a50-c9a1-4780-b81b-338969da5c70)
![image](https://github.com/user-attachments/assets/f75eb973-a11b-4199-9d6a-6adb92f8fba6)
![image](https://github.com/user-attachments/assets/338a15e4-7c95-4dd2-962c-07af2848b249)
![image](https://github.com/user-attachments/assets/b0241bdd-c599-47ef-a286-a47304ae65f8)
![image](https://github.com/user-attachments/assets/65f55d69-bf9d-485f-bc2c-41d1fe31e226)
![image](https://github.com/user-attachments/assets/2ec8dca1-044b-4ff6-806a-3eb8537b5992)

![image](https://github.com/user-attachments/assets/f7a522b6-83b2-480d-bde0-6686e81fac20)










