package it.unifi.dinfo.stlab;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.oristool.models.gspn.GSPNSteadyState;
import org.oristool.models.stpn.RewardRate;
import org.oristool.models.stpn.SteadyStateSolution;
import org.oristool.petrinet.Marking;
import org.oristool.petrinet.PetriNet;

// TODO: adding a new reward is complex
public class ReplicaSetModel {

    private PetriNet net;
    private Marking marking;

    private List<Endpoint> endpoints;
    private SteadyStateSolution<RewardRate> rewardsSolution;

    public ReplicaSetModel(PetriNet net, Marking marking, List<Endpoint> endpoints) {
        this.net = net;
        this.marking = marking;
        this.endpoints = endpoints;
    }

    public void analyze() {
        GSPNSteadyState analysis = GSPNSteadyState.builder().build();
        Map<Marking, Double> steadyStateMap = analysis.compute(net, marking);
        Map<Marking, BigDecimal> convertedSteadyStateMap = new HashMap<>();
        for (Map.Entry<Marking, Double> entry : steadyStateMap.entrySet()) {
            convertedSteadyStateMap.put(entry.getKey(), BigDecimal.valueOf(entry.getValue()));
        }
        SteadyStateSolution<Marking> solution = new SteadyStateSolution<>(convertedSteadyStateMap);
        System.out.println(rewardOfInterest());
        rewardsSolution = SteadyStateSolution.computeRewards(solution, rewardOfInterest());
    }

    private String rewardOfInterest() {
        String endpointsReliabilityRewards = getEndpointsReliabilityRewards();
        String endpointsUnavailabilityRewards = getEndpointsUnavailabilityRewards();
        String healthyComputationRewards = getEndpointsHealthyComputationReward();
        String resourceUsageReward = getResourceUsageReward();
        return endpointsReliabilityRewards + endpointsUnavailabilityRewards + healthyComputationRewards +
                resourceUsageReward;
    }

    public BigDecimal getSteadyStateResourceUsage() {
        Map<RewardRate, BigDecimal> steadyState = rewardsSolution.getSteadyState();
        BigDecimal resourceUsage = steadyState.entrySet().stream()
                .filter(t -> t.getKey().toString().equals(getResourceUsageReward())).findFirst().get().getValue();
        return resourceUsage;
    }

    public Map<Endpoint, BigDecimal> getSteadyStateEndpointsReliabilities() {
        Map<RewardRate, BigDecimal> steadyState = rewardsSolution.getSteadyState();
        Map<Endpoint, BigDecimal> reliabilties = new HashMap<>();
        for (Endpoint endpoint : endpoints) {
            reliabilties.put(endpoint,
                    steadyState.entrySet().stream()
                            .filter(t -> t.getKey().toString().equals(getSingleEndpointReliabilityReward(endpoint)))
                            .findFirst().get().getValue().multiply(BigDecimal.valueOf(endpoint.serviceRate()))
                            .multiply(BigDecimal.valueOf(endpoint.agedToFailedTendency())));
        }
        return reliabilties;
    }

    public Map<Endpoint, BigDecimal> getSteadyStateEndpointsUnavailiabilities() {
        Map<RewardRate, BigDecimal> steadyState = rewardsSolution.getSteadyState();
        Map<Endpoint, BigDecimal> unavailabilities = new HashMap<>();
        for (Endpoint endpoint : endpoints) {
            unavailabilities.put(endpoint,
                    steadyState.entrySet().stream()
                            .filter(t -> t.getKey().toString().equals(getSingleEndpointUnavailabilityReward(endpoint)))
                            .findFirst().get().getValue());
        }
        return unavailabilities;
    }

    public String getEndpointsUnavailabilityRewards() {
        String reward = "";
        for (Endpoint endpoint : endpoints) {
            reward += getSingleEndpointUnavailabilityReward(endpoint) + ";";
        }
        return reward;
    }

    public String getEndpointsHealthyComputationReward() {
        String reward = "";
        for (Endpoint endpoint : endpoints) {
            reward += getSingleEndpointHealthyComputationReward(endpoint) + ";";
        }
        return reward;
    }

    public Map<Endpoint, BigDecimal> getSteadyStateAgingContributions() {
        Map<RewardRate, BigDecimal> steadyState = rewardsSolution.getSteadyState();
        Map<Endpoint, BigDecimal> contributions = new HashMap<>();
        for (Endpoint endpoint : endpoints) {
            contributions.put(endpoint,
                    steadyState.entrySet().stream()
                            .filter(t -> t.getKey().toString().equals(getSingleEndpointReliabilityReward(endpoint)))
                            .findFirst().get().getValue().multiply(BigDecimal.valueOf(endpoint.serviceRate()))
                            .multiply(BigDecimal.valueOf(endpoint.healthyToAgedTendency())));
        }
        return contributions;
    }

    private String getSingleEndpointUnavailabilityReward(Endpoint endpoint) {
        return "If((Healthy+Aged)==0," + endpoint.arrivalRate() + ",0)";
    }

    private String getSingleEndpointHealthyComputationReward(Endpoint endpoint) {
        return "HealthyComputation" + endpoint.id();
    }

    public String getEndpointsReliabilityRewards() {
        String reward = "";
        for (Endpoint endpoint : endpoints) {
            reward += getSingleEndpointReliabilityReward(endpoint) + ";";
        }
        return reward;
    }

    private String getSingleEndpointReliabilityReward(Endpoint endpoint) {
        return "AgedComputation" + endpoint.id();
    }

    public String getResourceUsageReward() {
        return "Healthy+Aged";
    }

    public List<Endpoint> getEndpoints() {
        return endpoints;
    }

    public void setEndpoints(List<Endpoint> endpoints) {
        this.endpoints = endpoints;
    }


    @Deprecated
    private String getSingleEndpointReliabilityRewardOLD(Endpoint endpoint) {
        return endpoint.serviceRate() + "*AgedComputation" + endpoint.id() + "*"
                + endpoint.agedToFailedTendency() + ";";
    }

}
