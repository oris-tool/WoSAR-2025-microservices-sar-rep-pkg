package it.unifi.dinfo.stlab;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;

import org.oristool.models.pn.Priority;
import org.oristool.models.stpn.MarkingExpr;
import org.oristool.models.stpn.trees.StochasticTransitionFeature;
import org.oristool.petrinet.Marking;
import org.oristool.petrinet.PetriNet;
import org.oristool.petrinet.Place;
import org.oristool.petrinet.Transition;

public class ReplicaSetBuilder {

  private double repairRate;
  private double rejuvenationRate;
  private double falsePositiveProb;
  private double falseNegativeProb;
  private int numOfReplicas;

  public ReplicaSetModel build(Endpoint... endpoints) {
    PetriNet net = new PetriNet();
    Marking marking = new Marking();
    buildCoreModel(net, marking);
    for (Endpoint endpoint : endpoints) {
      attachEndpoint(net, marking, endpoint);
    }
    return new ReplicaSetModel(net, marking, new ArrayList<>(Arrays.asList(endpoints)));
  }

  private void buildCoreModel(PetriNet net, Marking marking) {
    // Fixed Places
    Place Aged = net.addPlace("Aged");
    Place AgedAtEnd = net.addPlace("AgedAtEnd");
    Place Failed = net.addPlace("Failed");
    Place Healthy = net.addPlace("Healthy");
    Place HealthyAtEnd = net.addPlace("HealthyAtEnd");
    Place Rejuvenating = net.addPlace("Rejuvenating");

    // Fixed Transitions
    Transition agedNoRej = net.addTransition("agedNoRej");
    Transition agedRej = net.addTransition("agedRej");
    Transition healthyNoRej = net.addTransition("healthyNoRej");
    Transition healthyRej = net.addTransition("healthyRej");
    Transition rejuvenate = net.addTransition("rejuvenate");
    Transition repair = net.addTransition("repair");

    // Fixed Connectors
    net.addPrecondition(AgedAtEnd, agedNoRej);
    net.addPostcondition(repair, Healthy);
    net.addPostcondition(healthyRej, Rejuvenating);
    net.addPostcondition(agedNoRej, Aged);
    net.addPrecondition(AgedAtEnd, agedRej);
    net.addPostcondition(healthyNoRej, Healthy);
    net.addPostcondition(rejuvenate, Healthy);
    net.addPrecondition(HealthyAtEnd, healthyNoRej);
    net.addPostcondition(agedRej, Rejuvenating);
    net.addPrecondition(Rejuvenating, rejuvenate);
    net.addPrecondition(HealthyAtEnd, healthyRej);
    net.addPrecondition(Failed, repair);

    // Fixed Tokens
    marking.setTokens(Healthy, this.numOfReplicas);
    marking.setTokens(Aged, 0);
    marking.setTokens(AgedAtEnd, 0);
    marking.setTokens(Failed, 0);
    marking.setTokens(HealthyAtEnd, 0);
    marking.setTokens(Rejuvenating, 0);

    // Fixed Features
    agedNoRej.addFeature(StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"),
        MarkingExpr.from(String.valueOf(falseNegativeProb), net)));
    agedNoRej.addFeature(new Priority(0));
    agedRej.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1", net)));
    agedRej.addFeature(new Priority(0));
    healthyNoRej.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1", net)));
    healthyNoRej.addFeature(new Priority(0));
    healthyRej.addFeature(StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"),
        MarkingExpr.from(String.valueOf(falsePositiveProb), net)));
    healthyRej.addFeature(new Priority(0));
    rejuvenate.addFeature(StochasticTransitionFeature.newExponentialInstance(new BigDecimal("1"),
        MarkingExpr.from(String.valueOf(rejuvenationRate) + "*Rejuvenating", net)));
    repair.addFeature(StochasticTransitionFeature.newExponentialInstance(new BigDecimal("1"),
        MarkingExpr.from(String.valueOf(repairRate) + "*Failed", net)));
  }

  private void attachEndpoint(PetriNet net, Marking marking, Endpoint endpoint) {

    Place Request = net.addPlace("Request" + endpoint.id());
    Place HealthyComputation = net.addPlace("HealthyComputation" + endpoint.id());
    Place AgedComputation = net.addPlace("AgedComputation" + endpoint.id());
    Place AgingSwitch = net.addPlace("AgingSwitch" + endpoint.id());
    Place FailingSwitch = net.addPlace("FailingSwitch" + endpoint.id());

    Transition agedComputation = net.addTransition("agedComputation" + endpoint.id());
    Transition agedReplicaSelected = net.addTransition("agedReplicaSelected" + endpoint.id());
    Transition agedToFailed = net.addTransition("agedToFailed" + endpoint.id());
    Transition arrival = net.addTransition("arrival" + endpoint.id());
    Transition backAged = net.addTransition("backAged" + endpoint.id());
    Transition backHealthy = net.addTransition("backHealthy" + endpoint.id());
    Transition healthyComputation = net.addTransition("healthyComputation" + endpoint.id());
    Transition healthyReplicaSelected = net.addTransition("healthyReplicaSelected" + endpoint.id());
    Transition healthyToAged = net.addTransition("healthyToAged" + endpoint.id());
    Transition reject = net.addTransition("reject" + endpoint.id());

    // Fixed Network Connection
    Place Healthy = net.getPlace("Healthy");
    net.addPrecondition(Healthy, healthyReplicaSelected);

    Place Aged = net.getPlace("Aged");
    net.addPrecondition(Aged, agedReplicaSelected);

    net.addPostcondition(arrival, Request);
    net.addPrecondition(Request, healthyReplicaSelected);
    net.addPrecondition(Request, agedReplicaSelected);
    net.addPrecondition(Request, reject);

    net.addPostcondition(healthyReplicaSelected, HealthyComputation);
    net.addPostcondition(agedReplicaSelected, AgedComputation);

    net.addPrecondition(HealthyComputation, healthyComputation);
    net.addPrecondition(AgedComputation, agedComputation);

    net.addPostcondition(healthyComputation, AgingSwitch);
    net.addPostcondition(agedComputation, FailingSwitch);

    net.addPrecondition(AgingSwitch, backHealthy);
    net.addPrecondition(AgingSwitch, healthyToAged);

    net.addPrecondition(FailingSwitch, backAged);
    net.addPrecondition(FailingSwitch, agedToFailed);

    // Fixed Network Connection
    Place Failed = net.getPlace("Failed");
    net.addPostcondition(agedToFailed, Failed);

    Place AgedAtEnd = net.getPlace("AgedAtEnd");
    net.addPostcondition(backAged, AgedAtEnd);
    net.addPostcondition(healthyToAged, AgedAtEnd);
    Place HealthyAtEnd = net.getPlace("HealthyAtEnd");
    net.addPostcondition(backHealthy, HealthyAtEnd);

    // Endpoint specific Properties
    marking.setTokens(AgedComputation, 0);
    marking.setTokens(AgingSwitch, 0);
    marking.setTokens(FailingSwitch, 0);
    marking.setTokens(HealthyComputation, 0);
    marking.setTokens(Request, 0);

    arrival.addFeature(StochasticTransitionFeature.newExponentialInstance(new BigDecimal("1"),
        MarkingExpr.from(String.valueOf(endpoint.arrivalRate()), net)));

    healthyReplicaSelected.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1*Healthy", net)));
    healthyReplicaSelected.addFeature(new Priority(1));

    agedReplicaSelected.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1*Aged", net)));
    agedReplicaSelected.addFeature(new Priority(1));

    reject.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1", net)));
    reject.addFeature(new Priority(0));

    healthyComputation.addFeature(StochasticTransitionFeature.newExponentialInstance(new BigDecimal("1"),
        MarkingExpr.from(String.valueOf(endpoint.serviceRate()) + "*HealthyComputation" + endpoint.id(), net)));
    agedComputation.addFeature(StochasticTransitionFeature.newExponentialInstance(new BigDecimal("1"),
        MarkingExpr.from(String.valueOf(endpoint.serviceRate()) + "*AgedComputation" + endpoint.id(), net)));

    backHealthy.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1", net)));
    backHealthy.addFeature(new Priority(0));

    healthyToAged.addFeature(StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"),
        MarkingExpr.from(String.valueOf(endpoint.healthyToAgedTendency()), net)));
    healthyToAged.addFeature(new Priority(0));

    backAged.addFeature(
        StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"), MarkingExpr.from("1", net)));
    backAged.addFeature(new Priority(0));

    agedToFailed.addFeature(StochasticTransitionFeature.newDeterministicInstance(new BigDecimal("0"),
        MarkingExpr.from(String.valueOf(endpoint.agedToFailedTendency()), net)));
    agedToFailed.addFeature(new Priority(0));

  }

  public double getRepairRate() {
    return repairRate;
  }

  public void setRepairRate(double repairRate) {
    this.repairRate = repairRate;
  }

  public double getRejuvenationRate() {
    return rejuvenationRate;
  }

  public void setRejuvenationRate(double rejuvenationRate) {
    this.rejuvenationRate = rejuvenationRate;
  }

  public double getFalsePositiveProb() {
    return falsePositiveProb;
  }

  public void setFalsePositiveProb(double falsePositiveProb) {
    this.falsePositiveProb = falsePositiveProb;
  }

  public double getFalseNegativeProb() {
    return falseNegativeProb;
  }

  public void setFalseNegativeProb(double falseNegativeProb) {
    this.falseNegativeProb = falseNegativeProb;
  }

  public int getNumOfReplicas() {
    return numOfReplicas;
  }

  public void setNumOfReplicas(int numOfReplicas) {
    this.numOfReplicas = numOfReplicas;
  }

}
